"""
Centralized LaunchDarkly API Client
High-performance, cached, and resilient API client for LaunchDarkly operations
"""

import requests
import json
import time
import logging
import csv
import os
from datetime import datetime, timedelta
from threading import Lock
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from functools import wraps
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from shared.config_loader import LAUNCHDARKLY_API_KEY, PROJECT_KEY
from api_config.api_endpoints import LAUNCHDARKLY_BASE_URL, APIConfig

@dataclass
class CacheEntry:
    """Cache entry with TTL"""
    data: Any
    timestamp: datetime
    ttl_seconds: int
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl_seconds)

class RateLimiter:
    """Token bucket rate limiter"""
    def __init__(self, rate_per_minute: int = 60):
        self.rate_per_minute = rate_per_minute
        self.tokens = rate_per_minute
        self.last_update = time.time()
        self.lock = Lock()
    
    def acquire(self) -> bool:
        with self.lock:
            now = time.time()
            # Add tokens based on elapsed time
            elapsed = now - self.last_update
            self.tokens = min(self.rate_per_minute, self.tokens + elapsed * (self.rate_per_minute / 60))
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
    
    def wait_time(self) -> float:
        """Get wait time until next token is available"""
        with self.lock:
            if self.tokens >= 1:
                return 0
            return (1 - self.tokens) * (60 / self.rate_per_minute)

class APICache:
    """Thread-safe API response cache with TTL"""
    def __init__(self):
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            entry = self.cache.get(key)
            if entry and not entry.is_expired:
                return entry.data
            elif entry:
                # Remove expired entry
                del self.cache[key]
            return None
    
    def set(self, key: str, data: Any, ttl_seconds: int = 300):
        with self.lock:
            self.cache[key] = CacheEntry(
                data=data,
                timestamp=datetime.now(),
                ttl_seconds=ttl_seconds
            )
    
    def clear(self):
        with self.lock:
            self.cache.clear()
    
    def remove(self, key: str):
        with self.lock:
            self.cache.pop(key, None)

def cached_request(ttl_seconds: int = 300):
    """Decorator for caching API requests"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache first
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(self, *args, **kwargs)
            if result is not None:
                self.cache.set(cache_key, result, ttl_seconds)
            
            return result
        return wrapper
    return decorator

class LaunchDarklyClient:
    """Centralized, high-performance LaunchDarkly API client"""
    
    def __init__(self, api_key: str = None, project_key: str = None):
        self.api_key = api_key or LAUNCHDARKLY_API_KEY
        self.project_key = project_key or PROJECT_KEY
        self.base_url = LAUNCHDARKLY_BASE_URL
        
        # Initialize session with connection pooling and retries
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PATCH", "PUT"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # Initialize cache and rate limiter
        self.cache = APICache()
        self.rate_limiter = RateLimiter(rate_per_minute=50)  # Conservative rate limit
        
        # Performance tracking
        self.stats = {
            "requests_made": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0
        }
        
        # Logger
        self.logger = logging.getLogger(__name__)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Make rate-limited HTTP request with error handling"""
        # Rate limiting
        if not self.rate_limiter.acquire():
            wait_time = self.rate_limiter.wait_time()
            if wait_time > 0:
                time.sleep(wait_time)
                if not self.rate_limiter.acquire():
                    raise Exception("Rate limit exceeded")
        
        self.stats["requests_made"] += 1
        
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(method, url, timeout=APIConfig.DEFAULT_TIMEOUT, **kwargs)
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            self.stats["errors"] += 1
            self.logger.error(f"API request failed: {method} {endpoint} - {str(e)}")
            raise
    
    @cached_request(ttl_seconds=300)  # 5-minute cache
    def get_all_flags(self, include_archived: bool = True, limit: int = 100, sort_by: str = "modified") -> List[Dict]:
        """Get all feature flags with caching, pagination, and smart sorting"""
        all_flags = []
        offset = 0
        
        while True:
            # Get flags - API doesn't provide environment data reliably
            endpoint = f"/flags/{self.project_key}?limit={limit}&offset={offset}&summary=0"
            
            response = self._make_request("GET", endpoint)
            if not response:
                break
                
            data = response.json()
            flags = data.get("items", [])
            
            all_flags.extend(flags)
            
            # Check if we have more pages
            if len(flags) < limit:
                break
            offset += limit
        
        # Enrich flags with additional metadata
        for flag in all_flags:
            self._enrich_flag_data(flag)
        
        # Smart sorting based on user preference
        return self._sort_flags(all_flags, sort_by)
    
    def _sort_flags(self, flags: List[Dict], sort_by: str) -> List[Dict]:
        """Sort flags based on specified criteria"""
        try:
            if sort_by == "modified":
                # Sort by last modified date (newest first)
                return sorted(flags, key=lambda x: x.get("lastModifiedDateTime", datetime.min), reverse=True)
            elif sort_by == "created":
                # Sort by creation date (newest first)
                return sorted(flags, key=lambda x: x.get("creationDateTime", datetime.min), reverse=True)
            elif sort_by == "name":
                # Sort alphabetically by name
                return sorted(flags, key=lambda x: x.get("name", "").lower())
            elif sort_by == "key":
                # Sort alphabetically by key
                return sorted(flags, key=lambda x: x.get("key", "").lower())
            elif sort_by == "health":
                # Sort by health score (highest first)
                return sorted(flags, key=lambda x: x.get("healthScore", 0), reverse=True)
            elif sort_by == "status":
                # Sort by status (Active first, then Archived)
                return sorted(flags, key=lambda x: (x.get("status", "") != "Active", x.get("name", "").lower()))
            else:
                # Default to modified date
                return sorted(flags, key=lambda x: x.get("lastModifiedDateTime", datetime.min), reverse=True)
        except Exception as e:
            self.logger.warning(f"Failed to sort flags by {sort_by}: {str(e)}")
            return flags
    
    def _enrich_flag_data(self, flag: Dict):
        """Enrich flag data with computed fields"""
        # Set flag status based on archived field
        flag["status"] = "Archived" if flag.get("archived", False) else "Active"
        
        # Calculate creation date
        creation_date = flag.get("creationDate")
        if creation_date:
            flag["creationDateTime"] = datetime.fromtimestamp(creation_date / 1000)
        
        # Find most recent modification across environments
        environments = flag.get("environments", {})
        latest_modified = 0
        
        # Environment data processing (reduced logging since we know API doesn't provide this data)
        flag_key = flag.get("key", "unknown")
        
        for env_key, env_data in environments.items():
            last_modified = env_data.get("lastModified", 0)
            if last_modified > latest_modified:
                latest_modified = last_modified
        
        # Fallback to creation date if no environment modifications
        if latest_modified:
            flag["lastModifiedDateTime"] = datetime.fromtimestamp(latest_modified / 1000)
        elif creation_date:
            flag["lastModifiedDateTime"] = flag["creationDateTime"]
        
        # Calculate flag health score
        flag["healthScore"] = self._calculate_health_score(flag)
        
        # Detect orphaned flags
        flag["isOrphaned"] = self._is_orphaned_flag(flag)
        
        # Calculate environment status
        flag["environmentStatus"] = self._get_environment_status(flag)
    
    def _calculate_health_score(self, flag: Dict) -> int:
        """Calculate flag health score (0-100)"""
        score = 100
        
        # Deduct points for missing description
        if not flag.get("description", "").strip():
            score -= 20
        
        # Deduct points for no tags
        if not flag.get("tags", []):
            score -= 10
        
        # Check if flag has rules/targeting
        environments = flag.get("environments", {})
        has_rules = False
        
        for env_data in environments.values():
            if env_data.get("rules", []) or env_data.get("targets", []):
                has_rules = True
                break
        
        if not has_rules:
            score -= 30
        
        # Check if flag is temporary but old
        if flag.get("temporary", False):
            creation_date = flag.get("creationDateTime")
            if creation_date and (datetime.now() - creation_date).days > 30:
                score -= 20
        
        return max(0, score)
    
    def _is_orphaned_flag(self, flag: Dict) -> bool:
        """Check if flag is orphaned (no rules, no targeting, not actively serving traffic)"""
        environments = flag.get("environments", {})
        
        # If no environment data available, assume flag is NOT orphaned (conservative approach)
        # Individual orphaned detection will be done on-demand when user selects orphaned filter
        if not environments:
            return False
        
        for env_data in environments.values():
            # Check for rules
            if env_data.get("rules", []):
                return False
            
            # Check for individual targeting
            if env_data.get("targets", []):
                return False
            
            # Check for context targets
            if env_data.get("contextTargets", []):
                return False
            
            # Check if flag is actively serving traffic (enabled with fallthrough)
            if env_data.get("on", False) and env_data.get("fallthrough"):
                return False
            
            # Check if flag is enabled at all
            if env_data.get("on", False):
                return False
        
        # Only mark as orphaned if we have environment data and confirmed no usage
        return True
    
    def export_orphaned_flags_bg(self, progress_callback=None, completion_callback=None):
        """
        Export orphaned flags to CSV in background with progress callbacks.
        
        Args:
            progress_callback: Function called with (current, total, flag_key) for progress updates
            completion_callback: Function called with (orphaned_flags, csv_filename) when complete
        """
        self.logger.info("ORPHANED EXPORT: Starting background orphaned flags detection...")
        
        try:
            # Get all flags from bulk API first
            bulk_flags = self.get_all_flags()
            flag_keys = [flag.get("key") for flag in bulk_flags if flag.get("key")]
            
            orphaned_flags = []
            total_flags = len(flag_keys)
            
            self.logger.info(f"ORPHANED EXPORT: Processing {total_flags} flags...")
            
            for i, flag_key in enumerate(flag_keys):
                try:
                    # Progress callback every flag (UI can choose to display every N)
                    if progress_callback:
                        progress_callback(i + 1, total_flags, flag_key)
                    
                    # Fetch individual flag with full environment data
                    individual_flag = self._get_individual_flag(flag_key)
                    
                    if individual_flag and individual_flag.get("environments"):
                        # Use the accurate orphaned detection with environment data
                        if self._is_orphaned_flag_with_env_data(individual_flag):
                            # Enrich flag data for export
                            enriched_flag = self._enrich_flag_for_export(individual_flag)
                            orphaned_flags.append(enriched_flag)
                            self.logger.warning(f"ORPHANED EXPORT: Found orphaned flag: {flag_key}")
                    
                except Exception as e:
                    self.logger.error(f"ORPHANED EXPORT: Error checking {flag_key}: {e}")
                    continue
            
            # Generate CSV export
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"orphaned_flags_{timestamp}.csv"
            
            self._write_orphaned_csv(orphaned_flags, filename)
            
            self.logger.info(f"ORPHANED EXPORT: Complete! Found {len(orphaned_flags)} orphaned flags")
            self.logger.info(f"ORPHANED EXPORT: Report saved to: {filename}")
            
            # Completion callback
            if completion_callback:
                completion_callback(orphaned_flags, filename)
                
            return orphaned_flags, filename
            
        except Exception as e:
            self.logger.error(f"ORPHANED EXPORT: Fatal error: {e}")
            if completion_callback:
                completion_callback(None, None, str(e))
            return None, None
    
    def _enrich_flag_for_export(self, flag: Dict) -> Dict:
        """Enrich flag data with export-friendly information"""
        enriched = flag.copy()
        environments = flag.get("environments", {})
        
        # Add environment summary
        env_summary = []
        for env_name, env_data in environments.items():
            enabled = "✅" if env_data.get("on", False) else "❌"
            env_summary.append(f"{env_data.get('_environmentName', env_name)}: {enabled}")
        
        enriched["environment_summary"] = " | ".join(env_summary)
        enriched["total_environments"] = len(environments)
        enriched["enabled_environments"] = len([e for e in environments.values() if e.get("on", False)])
        
        return enriched
    
    def _write_orphaned_csv(self, orphaned_flags: List[Dict], filename: str):
        """Write orphaned flags to CSV file"""
        if not orphaned_flags:
            # Create empty file with headers
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["No orphaned flags found", "All flags are actively used!"])
            return
        
        headers = [
            "Flag Key",
            "Flag Name", 
            "Description",
            "Tags",
            "Status",
            "Environment Summary",
            "Total Environments",
            "Enabled Environments",
            "Creation Date",
            "Last Modified",
            "Reason Orphaned"
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for flag in orphaned_flags:
                # Format dates
                created = flag.get("creationDate", 0)
                created_str = datetime.fromtimestamp(created/1000).strftime("%Y-%m-%d %H:%M") if created else "Unknown"
                
                modified = flag.get("lastModified", 0)
                modified_str = datetime.fromtimestamp(modified/1000).strftime("%Y-%m-%d %H:%M") if modified else "Unknown"
                
                # Determine why it's orphaned
                environments = flag.get("environments", {})
                reason_parts = []
                if not any(env.get("on", False) for env in environments.values()):
                    reason_parts.append("Disabled in all environments")
                if not any(env.get("rules", []) for env in environments.values()):
                    reason_parts.append("No targeting rules")
                if not any(env.get("targets", []) for env in environments.values()):
                    reason_parts.append("No individual targets")
                
                reason = " + ".join(reason_parts) if reason_parts else "Unknown"
                
                row = [
                    flag.get("key", ""),
                    flag.get("name", ""),
                    flag.get("description", ""),
                    " | ".join(flag.get("tags", [])),
                    "Archived" if flag.get("archived", False) else "Active",
                    flag.get("environment_summary", ""),
                    flag.get("total_environments", 0),
                    flag.get("enabled_environments", 0),
                    created_str,
                    modified_str,
                    reason
                ]
                writer.writerow(row)
    
    def _is_orphaned_flag_with_env_data(self, flag: Dict) -> bool:
        """Check if flag is orphaned using full environment data from individual API call"""
        environments = flag.get("environments", {})
        
        if not environments:
            return False
        
        for env_data in environments.values():
            # Check for rules
            if env_data.get("rules", []):
                return False
            
            # Check for individual targeting
            if env_data.get("targets", []):
                return False
            
            # Check for context targets
            if env_data.get("contextTargets", []):
                return False
            
            # Check if flag is actively serving traffic (enabled with fallthrough)
            if env_data.get("on", False) and env_data.get("fallthrough"):
                return False
            
            # Check if flag is enabled at all
            if env_data.get("on", False):
                return False
        
        # Only mark as orphaned if we have environment data and confirmed no usage
        return True
    
    def _get_individual_flag(self, flag_key: str) -> Dict:
        """Fetch individual flag with full environment data"""
        try:
            url = f"{self.base_url}/flags/{self.project_key}/{flag_key}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                self.logger.warning(f"Individual flag fetch failed for {flag_key}: {response.status_code}")
                return {}
        except Exception as e:
            self.logger.error(f"Individual flag fetch error for {flag_key}: {e}")
            return {}
    
    def _get_environment_status(self, flag: Dict) -> Dict[str, Dict]:
        """Get status for each environment"""
        environments = flag.get("environments", {})
        status = {}
        
        for env_key, env_data in environments.items():
            # Determine environment display name
            env_name = env_data.get("_environmentName", env_key.upper())
            
            status[env_name] = {
                "enabled": env_data.get("on", False),
                "archived": env_data.get("archived", False),
                "has_rules": bool(env_data.get("rules", [])),
                "has_targeting": bool(env_data.get("targets", []) or env_data.get("contextTargets", [])),
                "last_modified": env_data.get("lastModified", 0)
            }
        
        return status
    
    @cached_request(ttl_seconds=60)  # 1-minute cache for single flag
    def get_flag(self, flag_key: str) -> Optional[Dict]:
        """Get a specific flag"""
        endpoint = f"/flags/{self.project_key}/{flag_key}"
        response = self._make_request("GET", endpoint)
        
        if response:
            flag = response.json()
            self._enrich_flag_data(flag)
            return flag
        
        return None
    
    def test_orphaned_detection(self, flag_keys: list = None) -> Dict:
        """Test orphaned flag detection with individual flag calls"""
        if not flag_keys:
            # Test with first few flags from bulk list
            bulk_flags = self.get_all_flags(limit=10)
            flag_keys = [f.get("key") for f in bulk_flags[:5] if f.get("key")]
        
        results = {
            "tested_flags": [],
            "bulk_vs_individual": {},
            "orphaned_count": 0
        }
        
        self.logger.info("=== TESTING ORPHANED FLAG DETECTION ===")
        
        for flag_key in flag_keys:
            self.logger.info(f"Testing flag: {flag_key}")
            
            # Get individual flag details
            individual_flag = self.get_flag(flag_key)
            
            if individual_flag:
                environments = individual_flag.get("environments", {})
                is_orphaned = self._is_orphaned_flag(individual_flag)
                
                result = {
                    "flag_key": flag_key,
                    "has_environment_data": len(environments) > 0,
                    "environment_count": len(environments),
                    "is_orphaned": is_orphaned,
                    "environments": {}
                }
                
                # Analyze each environment
                for env_key, env_data in environments.items():
                    env_name = env_data.get("_environmentName", env_key)
                    result["environments"][env_name] = {
                        "enabled": env_data.get("on", False),
                        "has_rules": bool(env_data.get("rules", [])),
                        "has_targets": bool(env_data.get("targets", [])),
                        "has_context_targets": bool(env_data.get("contextTargets", [])),
                        "has_fallthrough": bool(env_data.get("fallthrough"))
                    }
                
                results["tested_flags"].append(result)
                if is_orphaned:
                    results["orphaned_count"] += 1
                    
                self.logger.info(f"  Environments: {len(environments)}")
                self.logger.info(f"  Orphaned: {is_orphaned}")
                
            else:
                self.logger.error("  Failed to fetch individual flag data")
        
        self.logger.info(f"SUMMARY: {results['orphaned_count']}/{len(flag_keys)} flags are orphaned")
        return results
    
    def update_flag(self, flag_key: str, environment: str, operations: List[Dict], comment: str = None) -> bool:
        """Update flag using semantic patch with user attribution"""
        from shared.user_session import get_api_comment
        
        endpoint = f"/flags/{self.project_key}/{flag_key}"
        
        # Generate comment with user attribution if not provided
        if not comment:
            comment = get_api_comment("Flag update")
        
        payload = {
            "environmentKey": environment,
            "comment": comment,
            "instructions": operations
        }
        
        try:
            response = self._make_request("PATCH", endpoint, json=payload)
            if response:
                # Invalidate cache for this flag
                self.cache.remove(f"get_flag:{hash(flag_key)}")
                self.cache.remove(f"get_all_flags:{hash('')}")  # Invalidate all flags cache
                return True
        except Exception as e:
            self.logger.error(f"Failed to update flag {flag_key}: {str(e)}")
        
        return False
    
    def create_flag(self, flag_data: Dict) -> bool:
        """Create a new flag"""
        endpoint = f"/flags/{self.project_key}"
        
        try:
            response = self._make_request("POST", endpoint, json=flag_data)
            if response:
                # Invalidate all flags cache
                self.cache.remove(f"get_all_flags:{hash('')}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to create flag: {str(e)}")
        
        return False
    
    def get_flag_statistics(self) -> Dict:
        """Get flag usage statistics"""
        flags = self.get_all_flags()
        
        stats = {
            "total_flags": len(flags),
            "active_flags": len([f for f in flags if f.get("status") == "Active"]),
            "archived_flags": len([f for f in flags if f.get("status") == "Archived"]),
            "orphaned_flags": len([f for f in flags if f.get("isOrphaned", False)]),
            "flags_with_rules": len([f for f in flags if not f.get("isOrphaned", False)]),
            "temporary_flags": len([f for f in flags if f.get("temporary", False)]),
            "health_score_avg": sum(f.get("healthScore", 0) for f in flags) / len(flags) if flags else 0,
            "recently_modified": len([f for f in flags if self._is_recently_modified(f)]),
            "environment_distribution": self._get_environment_distribution(flags)
        }
        
        return stats
    
    def _is_recently_modified(self, flag: Dict, days: int = 7) -> bool:
        """Check if flag was modified recently"""
        last_modified = flag.get("lastModifiedDateTime")
        if last_modified:
            return (datetime.now() - last_modified).days <= days
        return False
    
    def _get_environment_distribution(self, flags: List[Dict]) -> Dict:
        """Get distribution of flags across environments"""
        env_counts = {}
        
        for flag in flags:
            env_status = flag.get("environmentStatus", {})
            for env_name, status in env_status.items():
                if env_name not in env_counts:
                    env_counts[env_name] = {"total": 0, "enabled": 0, "disabled": 0}
                
                env_counts[env_name]["total"] += 1
                if status["enabled"]:
                    env_counts[env_name]["enabled"] += 1
                else:
                    env_counts[env_name]["disabled"] += 1
        
        return env_counts
    
    def get_performance_stats(self) -> Dict:
        """Get API client performance statistics"""
        cache_total = self.stats["cache_hits"] + self.stats["cache_misses"]
        cache_hit_rate = (self.stats["cache_hits"] / cache_total * 100) if cache_total > 0 else 0
        
        return {
            "requests_made": self.stats["requests_made"],
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "cache_hit_rate": round(cache_hit_rate, 2),
            "errors": self.stats["errors"],
            "cached_items": len(self.cache.cache)
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()

# Global instance
_client_instance = None

def get_client() -> LaunchDarklyClient:
    """Get singleton API client instance"""
    global _client_instance
    if _client_instance is None:
        _client_instance = LaunchDarklyClient()
    return _client_instance

def reset_client():
    """Reset client instance (useful for testing)"""
    global _client_instance
    if _client_instance:
        _client_instance.session.close()
    _client_instance = None
