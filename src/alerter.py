"""Alert mechanisms for PC duration violations."""

import json
import requests
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass


@dataclass
class AlertConfig:
    """Configuration for alert destinations."""
    webhook_url: Optional[str] = None
    email_recipients: Optional[list[str]] = None
    console_output: bool = True


class Alerter:
    """Handles sending alerts through various channels."""
    
    def __init__(self, config: AlertConfig):
        """Initialize the alerter.
        
        Args:
            config: Alert configuration
        """
        self.config = config
    
    def send_alert(self, alert_data: dict) -> dict:
        """Send an alert through all configured channels.
        
        Args:
            alert_data: Alert payload to send
            
        Returns:
            Dictionary with results from each channel
        """
        results = {
            "console": False,
            "webhook": False,
            "email": False,
            "errors": []
        }
        
        # Console output
        if self.config.console_output:
            try:
                self._send_console_alert(alert_data)
                results["console"] = True
            except Exception as e:
                results["errors"].append(f"Console error: {str(e)}")
        
        # Webhook
        if self.config.webhook_url:
            try:
                self._send_webhook_alert(alert_data)
                results["webhook"] = True
            except Exception as e:
                results["errors"].append(f"Webhook error: {str(e)}")
        
        # Email (placeholder - would need SMTP or email service integration)
        if self.config.email_recipients:
            try:
                self._send_email_alert(alert_data)
                results["email"] = True
            except Exception as e:
                results["errors"].append(f"Email error: {str(e)}")
        
        return results
    
    def _send_console_alert(self, alert_data: dict) -> None:
        """Output alert to console/logs.
        
        Args:
            alert_data: Alert payload
        """
        driver_name = alert_data.get("driver_name", "Unknown")
        pc_hours = alert_data.get("consecutive_pc_hours", 0)
        threshold = alert_data.get("threshold_hours", 16)
        pc_start = alert_data.get("pc_start_time", "Unknown")
        
        print("=" * 60)
        print("🚨 PC DURATION ALERT")
        print("=" * 60)
        print(f"Driver: {driver_name}")
        print(f"Driver ID: {alert_data.get('driver_id', 'Unknown')}")
        print(f"Consecutive PC Hours: {pc_hours:.2f}")
        print(f"Threshold: {threshold} hours")
        print(f"PC Started: {pc_start}")
        print(f"Alert Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 60)
    
    def _send_webhook_alert(self, alert_data: dict) -> None:
        """Send alert to webhook URL.
        
        Args:
            alert_data: Alert payload
        """
        if not self.config.webhook_url:
            return
        
        payload = {
            "alert_type": "pc_duration_exceeded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **alert_data
        }
        
        response = requests.post(
            self.config.webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        print(f"✅ Webhook alert sent successfully to {self.config.webhook_url}")
    
    def _send_email_alert(self, alert_data: dict) -> None:
        """Send alert via email.
        
        Note: This is a placeholder. In production, integrate with
        an email service like SendGrid, SES, or SMTP.
        
        Args:
            alert_data: Alert payload
        """
        if not self.config.email_recipients:
            return
        
        # Placeholder - log what would be sent
        driver_name = alert_data.get("driver_name", "Unknown")
        pc_hours = alert_data.get("consecutive_pc_hours", 0)
        
        print(f"📧 Email alert would be sent to: {', '.join(self.config.email_recipients)}")
        print(f"   Subject: PC Duration Alert - {driver_name}")
        print(f"   Body: Driver has been in PC for {pc_hours:.2f} hours")
        
        # TODO: Implement actual email sending
        # Example with SendGrid:
        # from sendgrid import SendGridAPIClient
        # sg = SendGridAPIClient(api_key)
        # sg.send(message)
    
    def send_bulk_alerts(self, alerts: list[dict]) -> dict:
        """Send multiple alerts.
        
        Args:
            alerts: List of alert payloads
            
        Returns:
            Summary of all alert results
        """
        summary = {
            "total_alerts": len(alerts),
            "successful": 0,
            "failed": 0,
            "results": []
        }
        
        for alert_data in alerts:
            result = self.send_alert(alert_data)
            summary["results"].append(result)
            
            if not result["errors"]:
                summary["successful"] += 1
            else:
                summary["failed"] += 1
        
        return summary
    
    def send_summary(self, analysis_summary: dict) -> None:
        """Send a summary of the analysis run.
        
        Args:
            analysis_summary: Summary data from the analysis
        """
        if self.config.console_output:
            print("\n" + "=" * 60)
            print("📊 PC DURATION ANALYSIS SUMMARY")
            print("=" * 60)
            print(f"Drivers Checked: {analysis_summary.get('drivers_checked', 0)}")
            print(f"Drivers in PC: {analysis_summary.get('drivers_in_pc', 0)}")
            print(f"Alerts Triggered: {analysis_summary.get('alerts_triggered', 0)}")
            print(f"Threshold: {analysis_summary.get('threshold_hours', 16)} hours")
            print("=" * 60 + "\n")

