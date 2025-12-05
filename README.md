# PC Duration Alert - Samsara Function

Monitors drivers' Hours of Service (HOS) status and alerts when a driver has been in **Personal Conveyance (PC)** status for more than 16 consecutive hours (configurable).

## Files

| File | Purpose |
|------|---------|
| `entrypoint.py` | Main handler function |
| `samsarafnsecrets.py` | Secrets helper (AWS SSM) |

## Handler

```
entrypoint.main
```

## Secrets Required

Add in the Samsara Functions UI under "Secrets":

| Key | Description |
|-----|-------------|
| `SAMSARA_API_KEY` | Your Samsara API token |

## Event Parameters (Optional)

Pass in the event body or as Event Parameters:

```json
{
  "pc_threshold_hours": 16
}
```

## Response

```json
{
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
      "hours_in_pc": 18.5,
      "pc_start_time": "2025-12-01T05:30:00Z"
    }
  ]
}
```

## Deployment

1. Create zip: `zip pc-alert.zip entrypoint.py samsarafnsecrets.py`
2. Upload to Samsara Functions
3. Set handler to `entrypoint.main`
4. Add `SAMSARA_API_KEY` secret
5. Run!

## Dependencies

Uses packages from the Samsara Functions Lambda Layer:
- `boto3` - AWS SDK for SSM secrets
- `requests` - HTTP client for Samsara API
