"""Main handler for the PC Duration Alert function."""

import os
from datetime import datetime, timezone
from typing import Optional

from .samsara_client import SamsaraClient
from .pc_analyzer import PCAnalyzer
from .alerter import Alerter, AlertConfig


# Default configuration values
DEFAULT_PC_THRESHOLD_HOURS = 16.0


def get_config(event: dict) -> dict:
    """Extract configuration from event or environment.
    
    Args:
        event: Event payload from function invocation
        
    Returns:
        Configuration dictionary
    """
    # Get from event body first, fall back to environment variables
    body = event.get("body", {})
    if isinstance(body, str):
        import json
        try:
            body = json.loads(body)
        except (json.JSONDecodeError, TypeError):
            body = {}
    
    return {
        "pc_threshold_hours": float(
            body.get("pc_threshold_hours") or 
            os.environ.get("PC_THRESHOLD_HOURS", DEFAULT_PC_THRESHOLD_HOURS)
        ),
        "driver_tag_ids": (
            body.get("driver_tag_ids") or 
            os.environ.get("DRIVER_TAG_IDS", "").split(",") 
            if os.environ.get("DRIVER_TAG_IDS") else None
        ),
        "webhook_url": (
            body.get("webhook_url") or 
            os.environ.get("WEBHOOK_URL")
        ),
        "email_recipients": (
            body.get("email_recipients") or 
            os.environ.get("EMAIL_RECIPIENTS", "").split(",")
            if os.environ.get("EMAIL_RECIPIENTS") else None
        )
    }


def main(event: dict, context: dict) -> dict:
    """Main handler function for PC Duration Alert.
    
    Monitors drivers' HOS status and alerts when a driver has been in
    Personal Conveyance (PC) status for more than the configured threshold.
    
    Uses the /fleet/hos/clocks endpoint which provides current duty status
    and when the driver entered that status.
    
    See: https://developers.samsara.com/reference/gethosclocks
    
    Args:
        event: Event payload containing optional configuration overrides
        context: Samsara function context with API token
        
    Returns:
        Response with analysis summary and any alerts triggered
    """
    print("🚛 Starting PC Duration Alert Monitor...")
    
    # Get API token from context
    api_token = context.get("samsara_api_token")
    if not api_token:
        return {
            "statusCode": 401,
            "body": {
                "error": "Missing Samsara API token in context"
            }
        }
    
    # Load configuration
    config = get_config(event)
    print(f"📋 Configuration:")
    print(f"   - PC Threshold: {config['pc_threshold_hours']} hours")
    print(f"   - Driver Tag Filter: {config['driver_tag_ids'] or 'All drivers'}")
    
    # Initialize clients
    samsara = SamsaraClient(api_token)
    analyzer = PCAnalyzer(threshold_hours=config["pc_threshold_hours"])
    alerter = Alerter(AlertConfig(
        webhook_url=config["webhook_url"],
        email_recipients=config["email_recipients"],
        console_output=True
    ))
    
    try:
        # Step 1: Fetch HOS clocks (includes current duty status for all drivers)
        print("\n📥 Fetching HOS clocks...")
        hos_clocks = samsara.get_hos_clocks(tag_ids=config["driver_tag_ids"])
        print(f"   Retrieved clocks for {len(hos_clocks)} drivers")
        
        if not hos_clocks:
            return {
                "statusCode": 200,
                "body": {
                    "message": "No drivers found",
                    "drivers_checked": 0,
                    "alerts_triggered": 0
                }
            }
        
        # Step 2: Analyze PC duration for each driver
        current_time = datetime.now(timezone.utc)
        print("\n🔍 Analyzing PC duration...")
        results = analyzer.analyze_all_clocks(hos_clocks, current_time)
        
        # Get drivers currently in PC
        drivers_in_pc = [r for r in results if r.is_currently_in_pc]
        print(f"   {len(drivers_in_pc)} drivers currently in PC")
        
        # Step 3: Get alerts (those exceeding threshold)
        alerts = analyzer.get_alerts(results)
        print(f"   {len(alerts)} drivers exceeding {config['pc_threshold_hours']} hour threshold")
        
        # Step 4: Send alerts
        alert_results = None
        if alerts:
            print("\n🚨 Sending alerts...")
            alert_payloads = [alert.to_dict() for alert in alerts]
            alert_results = alerter.send_bulk_alerts(alert_payloads)
        
        # Step 5: Send summary
        summary = {
            "drivers_checked": len(hos_clocks),
            "drivers_in_pc": len(drivers_in_pc),
            "alerts_triggered": len(alerts),
            "threshold_hours": config["pc_threshold_hours"]
        }
        alerter.send_summary(summary)
        
        # Build response
        response_body = {
            "success": True,
            "summary": summary,
            "alerts": [alert.to_dict() for alert in alerts],
            "alert_delivery": alert_results
        }
        
        # Include all PC drivers in detailed mode
        if event.get("body", {}).get("include_all_pc_drivers"):
            response_body["all_pc_drivers"] = [
                r.to_dict() for r in drivers_in_pc
            ]
        
        return {
            "statusCode": 200,
            "body": response_body
        }
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "statusCode": 500,
            "body": {
                "error": str(e),
                "message": "Failed to analyze PC duration"
            }
        }
