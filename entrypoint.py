"""PC Duration Alert - Monitors drivers in Personal Conveyance status."""
import os
import json
import requests
from datetime import datetime, timezone
from samsarafnsecrets import get_secrets

DEFAULT_PC_THRESHOLD = 16.0

def get_hos_clocks(api_token):
    """Fetch HOS clocks from Samsara API."""
    headers = {"Authorization": f"Bearer {api_token}"}
    clocks = []
    url = "https://api.samsara.com/fleet/hos/clocks"
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        clocks.extend(data.get("data", []))
        pagination = data.get("pagination", {})
        url = f"https://api.samsara.com/fleet/hos/clocks?after={pagination.get('endCursor')}" if pagination.get("hasNextPage") else None
    return clocks

def main(event, _):
    """Main handler - Handler: entrypoint.main"""
    corr_id = event.get("SamsaraFunctionCorrelationId", "unknown")
    print(corr_id, "PC Duration Alert started")
    
    # 1. Load secrets from SSM
    try:
        secrets = get_secrets()
        print(corr_id, f"Loaded {len(secrets)} secrets: {list(secrets.keys())}")
    except Exception as e:
        secrets = {}
        print(corr_id, f"Secrets error: {e}")
    
    # 2. Get API token (secrets -> event param -> env var)
    api_token = (
        secrets.get("SAMSARA_API_KEY") or 
        secrets.get("SAMSARA_API_TOKEN") or 
        event.get("api_key") or 
        os.environ.get("SAMSARA_API_KEY")
    )
    
    if not api_token:
        print(corr_id, "No API key found")
        return {"error": "No API key", "secrets_found": list(secrets.keys())}
    
    # 3. Get config
    threshold = float(event.get("pc_threshold_hours", DEFAULT_PC_THRESHOLD))
    print(corr_id, f"Threshold: {threshold} hours")
    
    # 4. Fetch HOS clocks
    try:
        clocks = get_hos_clocks(api_token)
        print(corr_id, f"Retrieved {len(clocks)} driver clocks")
    except Exception as e:
        print(corr_id, f"API error: {e}")
        return {"error": str(e)}
    
    # 5. Analyze for PC duration
    alerts = []
    drivers_in_pc = 0
    now = datetime.now(timezone.utc)
    
    for clock in clocks:
        driver = clock.get("driver", {})
        status = clock.get("currentDutyStatus", {})
        if status.get("hosStatusType") == "personalConveyance":
            drivers_in_pc += 1
            start_str = status.get("hosStatusStartTime")
            if start_str:
                try:
                    hours = (now - datetime.fromisoformat(start_str.replace("Z", "+00:00"))).total_seconds() / 3600
                    if hours >= threshold:
                        alerts.append({
                            "driver_id": driver.get("id"),
                            "driver_name": driver.get("name"),
                            "hours_in_pc": round(hours, 2),
                            "pc_start_time": start_str
                        })
                except Exception as e:
                    print(corr_id, f"Parse error: {e}")
    
    # Build list of driver names in violation for easy visibility
    drivers_in_violation = [f"{a['driver_name']} ({a['hours_in_pc']}h)" for a in alerts]
    
    result = {
        "success": True,
        "summary": {
            "drivers_checked": len(clocks),
            "drivers_in_pc": drivers_in_pc,
            "alerts_triggered": len(alerts),
            "threshold_hours": threshold,
            "drivers_in_violation": drivers_in_violation
        },
        "alerts": alerts
    }
    
    # Log driver names who are in violation
    if alerts:
        print(corr_id, f"⚠️ ALERTS: {', '.join(drivers_in_violation)}")
    
    print(corr_id, "PC Duration Alert finished", result["summary"])
    return result
