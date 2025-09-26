import requests
import logging
from api_config.api_endpoints import FeatureFlagEndpoints, APIHeaders, APIConfig, URLBuilder, LAUNCHDARKLY_BASE_URL
from shared.constants import ENVIRONMENT_MAPPINGS
from shared.config_loader import LOG_FILE

# Module logger (configuration is handled by the main app)
logger = logging.getLogger(__name__)

def _sanitize_headers(headers: dict) -> dict:
    """Redact sensitive headers before logging."""
    try:
        safe = dict(headers) if headers else {}
        for k in list(safe.keys()):
            lk = k.lower()
            if lk in ("authorization", "cookie", "set-cookie"):
                safe[k] = "***REDACTED***"
        return safe
    except Exception:
        return {"info": "unavailable"}

def get_authentication_token(parsed_url, query_params, pmc_id, site_id):
    auth_url = f"{parsed_url.scheme}://{parsed_url.netloc}/api/core/authentication/login"
    logger.debug(f"Auth URL: {auth_url}")
    if pmc_id and not site_id:
        site_id = pmc_id
    
    auth_form_data = {
        "grant_type": "password",
        "username": query_params.get("QTPLogon", [""])[0] or query_params.get("username", [""])[0],
        "password": query_params.get("QTPPassword", [""])[0] or query_params.get("password", [""])[0],
        "sessionGuid": "abc",
        "client_id": "os_web",
        "pmc_id": pmc_id if pmc_id else 0,
        "site_id": site_id if site_id else 0
    }
    
    for attempt in range(3):
        try:
            auth_response = requests.post(
                auth_url,
                data=auth_form_data,
                timeout=APIConfig.DEFAULT_TIMEOUT
            )
            auth_response.raise_for_status()
            return auth_response.json()['access_token']
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication API call failed (attempt {attempt + 1}): {e}")
    
    logger.error("Authentication failed after 3 attempts.")
    return None

def get_feature_flag_data(parsed_url, feature_flag_key, auth_token, app_context):
    feature_flag_url = f"{parsed_url.scheme}://{parsed_url.netloc}/api/featureflags/v1/launchdarkly/enabled/{feature_flag_key}"
    headers = {"Authorization": f"Bearer {auth_token}"}
    if app_context:
        headers["appcontext"] = app_context

    for attempt in range(3):
        try:
            response = requests.get(
                feature_flag_url,
                headers=headers,
                timeout=APIConfig.DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Feature Flag API call failed (attempt {attempt + 1}): {e}")

    return None

def update_flag(env_key, feature_key, update_value):
    from shared.config_loader import LAUNCHDARKLY_API_KEY, PROJECT_KEY
    from shared.user_session import get_api_comment

    api_key = LAUNCHDARKLY_API_KEY
    project_key = PROJECT_KEY
    operation = f"Flag {'enabled' if update_value else 'disabled'}"
    comment = get_api_comment(operation)
    
    # Map the UI environment key to the actual LaunchDarkly environment key
    actual_env_key = ENVIRONMENT_MAPPINGS.get(env_key, env_key)
    
    # Build URL correctly: project_key/feature_key (not environment)
    url = f"{LAUNCHDARKLY_BASE_URL}/flags/{project_key}/{feature_key}"
    
    headers = APIHeaders.get_launchdarkly_headers(api_key)
    headers["Content-Type"] = "application/json; domain-model=launchdarkly.semanticpatch"
    instruction_kind = "turnFlagOn" if update_value else "turnFlagOff"
    payload = {
        "environmentKey": actual_env_key,
        "comment": comment,
        "instructions": [
            {"kind": instruction_kind}
        ]
    }
    
    # Debug logging for request details (redacted & at DEBUG level)
    logger.debug(f"Request URL: {url}")
    logger.debug(f"Request Headers: {_sanitize_headers(headers)}")
    logger.debug(f"Request Payload: {payload}")

    for attempt in range(APIConfig.MAX_RETRIES):
        try:
            ld_response = requests.patch(
                url, 
                headers=headers, 
                json=payload, 
                timeout=APIConfig.DEFAULT_TIMEOUT
            )
            
            # Debug logging for response (at DEBUG level; redact cookies if present)
            logger.debug(f"Response Status: {ld_response.status_code}")
            logger.debug(f"Response Headers: {_sanitize_headers(dict(ld_response.headers))}")
            logger.debug(f"Response Body: {ld_response.text}")
            
            ld_response.raise_for_status()
            logger.info(
                f"Success: Feature flag '{feature_key}' {'turned ON' if update_value else 'turned OFF'}."
            )
            return True
        except requests.exceptions.Timeout:
            logger.error(f"Update Feature Flag API call timed out (attempt {attempt + 1})")
        except requests.exceptions.RequestException as e:
            logger.error(f"Update Feature Flag API call failed (attempt {attempt + 1}): {e}")
            # Log the full error details
            logger.error(f"Full error details: {e}")

    logger.error(f"Failed to update flag '{feature_key}' after {APIConfig.MAX_RETRIES} attempts.")
    return False

def get_environments():
    """Get available environments from LaunchDarkly project"""
    from shared.config_loader import LAUNCHDARKLY_API_KEY, PROJECT_KEY
    api_key = LAUNCHDARKLY_API_KEY
    project_key = PROJECT_KEY
    headers = APIHeaders.get_launchdarkly_headers(api_key)
    
    url = f"{LAUNCHDARKLY_BASE_URL}/projects/{project_key}/environments"
    
    try:
        response = requests.get(
            url, 
            headers=headers, 
            timeout=APIConfig.DEFAULT_TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            environments = []
            for env in data.get("items", []):
                environments.append(env.get("key", ""))
            return environments
        else:
            logger.error(f"Failed to get environments: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error getting environments: {e}")
        return []

def get_all_feature_flags():
    from shared.config_loader import LAUNCHDARKLY_API_KEY, PROJECT_KEY
    api_key = LAUNCHDARKLY_API_KEY
    project_key = PROJECT_KEY
    headers = APIHeaders.get_launchdarkly_headers(api_key)

    all_flags_data = []
    # Start with the base URL for the first request, ensuring full flag data is returned
    url = FeatureFlagEndpoints.GET_ALL_FLAGS + f"/{project_key}?limit=100&summary=0"

    while url:
        try:
            response = requests.get(
                url, 
                headers=headers, 
                timeout=APIConfig.DEFAULT_TIMEOUT
            )
            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
            
            data = response.json()
            all_flags_data.extend(data.get("items", []))
            
            # Check for a 'next' link to handle pagination
            next_link = data.get("_links", {}).get("next", {}).get("href")
            if next_link:
                url = f"https://app.launchdarkly.com{next_link}"
            else:
                url = None # No more pages
        except requests.exceptions.Timeout:
            logger.error("API request timed out while fetching all flags")
            break
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching all flags: {e}")
            break

    flags_list = []
    for flag in all_flags_data:
        # --- DEBUG: Log the raw environment data for a flag ---
        logger.debug(f"Flag: {flag.get('key')}, Environments: {flag.get('environments')}")
        # --- END DEBUG ---
        environments = flag.get("environments", {})
        flags_list.append({
            "key": flag.get("key", ""),
            "name": flag.get("name", ""),
            "dev": "ON" if environments.get("dev", {}).get("on", False) else "OFF",
            "qa": "ON" if environments.get("qa", {}).get("on", False) else "OFF",
            "staging": "ON" if environments.get("staging", {}).get("on", False) else "OFF",
            "prod": "ON" if environments.get("prod", {}).get("on", False) else "OFF",
        })

    return flags_list
