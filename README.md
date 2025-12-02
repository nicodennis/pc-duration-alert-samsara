# Duty Status Alert - PC Duration Monitor

Monitors drivers' Hours of Service (HOS) status and alerts when a driver has been in **Personal Conveyance (PC)** status for more than 16 consecutive hours (configurable).

## How It Works

1. **Fetches HOS clocks** for all drivers via [`/fleet/hos/clocks`](https://developers.samsara.com/reference/gethosclocks)
2. **Checks current duty status** - identifies drivers in `personalConveyance` status
3. **Calculates duration** from when they entered PC status to now
4. **Alerts** via console, webhook, and/or email when a driver exceeds the threshold

## Configuration

| Parameter | Description | Default | Source |
|-----------|-------------|---------|--------|
| `pc_threshold_hours` | Alert if PC exceeds this (hours) | `16` | Event body or `PC_THRESHOLD_HOURS` env |
| `driver_tag_ids` | Filter drivers by tag IDs | All drivers | Event body or `DRIVER_TAG_IDS` env |
| `webhook_url` | Send alerts to this webhook | None | Event body or `WEBHOOK_URL` env |
| `email_recipients` | Send email alerts to these addresses | None | Event body or `EMAIL_RECIPIENTS` env |

## Usage

### Basic Invocation

The function runs with default settings (16-hour threshold):

```json
{
  "body": {}
}
```

### Custom Configuration

Override defaults via the event body:

```json
{
  "body": {
    "pc_threshold_hours": 12,
    "driver_tag_ids": ["tag-123", "tag-456"],
    "webhook_url": "https://your-webhook.com/alerts",
    "include_all_pc_drivers": true
  }
}
```

## Response

### Success Response

```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "summary": {
      "drivers_checked": 50,
      "drivers_in_pc": 3,
      "alerts_triggered": 1,
      "threshold_hours": 16
    },
    "alerts": [
      {
        "driver_id": "123456",
        "driver_name": "John Doe",
        "is_currently_in_pc": true,
        "consecutive_pc_hours": 18.5,
        "pc_start_time": "2025-12-01T05:30:00+00:00",
        "exceeds_threshold": true,
        "threshold_hours": 16
      }
    ],
    "alert_delivery": {
      "total_alerts": 1,
      "successful": 1,
      "failed": 0
    }
  }
}
```

## Project Structure

```
src/
├── __init__.py         # Package marker
├── handler.py          # Main entry point
├── samsara_client.py   # Samsara API client
├── pc_analyzer.py      # PC duration analysis logic
└── alerter.py          # Alert delivery (console, webhook, email)
```

## Samsara API Endpoint Used

| Endpoint | Purpose |
|----------|---------|
| [`GET /fleet/hos/clocks`](https://developers.samsara.com/reference/gethosclocks) | Get current HOS status for all drivers |

The `/fleet/hos/clocks` endpoint returns:
- `currentDutyStatus.hosStatusType` - Current status (`personalConveyance`, `driving`, etc.)
- `currentDutyStatus.hosStatusStartTime` - When the driver entered this status

## Alert Channels

### Console
Always enabled. Outputs formatted alerts to stdout/logs.

### Webhook
POST request with JSON payload:

```json
{
  "alert_type": "pc_duration_exceeded",
  "timestamp": "2025-12-02T12:00:00+00:00",
  "driver_id": "123456",
  "driver_name": "John Doe",
  "consecutive_pc_hours": 18.5,
  "threshold_hours": 16,
  "pc_start_time": "2025-12-01T05:30:00+00:00"
}
```

### Email
Placeholder implementation - configure your preferred email service (SendGrid, SES, SMTP) in `src/alerter.py`.

## Dependencies

- `requests>=2.31.0` - HTTP client for Samsara API calls
