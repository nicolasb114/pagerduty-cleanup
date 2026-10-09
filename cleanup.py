#!/usr/bin/env python3
import json
import urllib.request
import urllib.error
import sys

CONFIG_FILE = "config.json"

def load_config():
    """Loads configuration parameters from config.json."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f" [ERROR] Configuration file '{CONFIG_FILE}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f" [ERROR] '{CONFIG_FILE}' contains invalid JSON formatting.")
        sys.exit(1)

def pd_api_request(url, method="GET", api_key=""):
    """Handles HTTP communication with PagerDuty API using standard libraries."""
    req = urllib.request.Request(url, method=method)
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Token token={api_key}")
    
    try:
        with urllib.request.urlopen(req) as response:
            if method == "DELETE":
                return True
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  [HTTP ERROR] Status {e.code}: {e.reason} for URL: {url}")
        try:
            err_body = e.read().decode("utf-8")
            print(f"  [DETAILS] {err_body}")
        except Exception:
            pass
        return None
    except Exception as e:
        print(f"  [SYSTEM ERROR] Failed execution on {url}. Error: {e}")
        return None

def fetch_all_resources(resource_type, api_key):
    """Paginates dynamically through PagerDuty API to pull all items."""
    all_resources = []
    offset = 0
    limit = 100  # Optimized pagination limit supported by PagerDuty
    has_more = True
    
    print(f"\n Fetching all {resource_type}...")
    while has_more:
        url = f"https://api.pagerduty.com/{resource_type}?limit={limit}&offset={offset}"
        data = pd_api_request(url, "GET", api_key)
        
        if not data or resource_type not in data:
            print(f" [ERROR] Could not retrieve data for {resource_type}.")
            break
            
        batch = data[resource_type]
        all_resources.extend(batch)
        print(f"  -> Retrieved {len(batch)} items (Total gathered so far: {len(all_resources)})")
        
        has_more = data.get("more", False)
        offset += limit
        
    return all_resources

def process_cleanup(resource_type, config):
    """Evaluates filter conditions and deletes matched items sequentially."""
    settings = config["cleanup_settings"].get(resource_type)
    if not settings or not settings.get("enabled", False):
        print(f"\n[-] Skipping {resource_type} cleanup (Disabled in config).")
        return

    prefix = settings.get("name_starts_with", "")
    dry_run = config.get("dry_run", True)
    api_key = config.get("api_key", "")

    # Fetch items from instance
    items = fetch_all_resources(resource_type, api_key)
    if not items:
        print(f" No {resource_type} found to process.")
        return

    # Filter items matching criteria
    matched_items = [i for i in items if i.get("name", "").startswith(prefix)]
    print(f"\n Found {len(matched_items)} out of {len(items)} {resource_type} matching prefix '{prefix}'")

    if not matched_items:
        return

    # Execute Deletions
    action_label = "[DRY RUN] Would delete" if dry_run else "[DELETING]"
    success_count = 0

    for index, item in enumerate(matched_items, start=1):
        item_id = item.get("id")
        item_name = item.get("name")
        
        print(f"  {action_label} {index}/{len(matched_items)}: {item_name} ({item_id})")
        
        if not dry_run:
            delete_url = f"https://api.pagerduty.com/{resource_type}/{item_id}"
            success = pd_api_request(delete_url, "DELETE", api_key)
            if success:
                success_count += 1
            # Graceful pacing inside deletion loop
    
    if not dry_run:
        print(f" Completed cleanup! Successfully removed {success_count}/{len(matched_items)} {resource_type}.")
    else:
        print(f" Dry Run mode complete for {resource_type}. No architectural mutations were performed.")

def main():
    print("==================================================")
    print("    PAGERDUTY INSTANCE DEMO CLEANUP UTILITY       ")
    print("==================================================")
    
    config = load_config()
    
    if config.get("dry_run", True):
        print("\n[!] SAFE MODE ENABLED: Running in DRY RUN mode.")
    else:
        print("\n[WARNING] LIVE MODE ACTIVE: Targets matching conditions will be PERMANENTLY ERASED.")
    
    # 1. Clean Services First (Cascades webhooks down automatically & isolates EPs)
    process_cleanup("services", config)
    
    # 2. Clean Escalation Policies Second (Safely freed from active service maps)
    process_cleanup("escalation_policies", config)

    print("\n==================================================")
    print("               CLEANUP PROCESS END                ")
    print("==================================================")

if __name__ == "__main__":
    main()