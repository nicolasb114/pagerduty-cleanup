# PagerDuty Sales Cycle Demo Environment Cleanup Tool

This zero-dependency Python tool automates the cleanup of test and demonstration assets inside a PagerDuty instance. It safely structures processes across high-volume footprints ($300+$ Services, $400+$ Escalation Policies).

## Architectural Design Decisions

* **No Third-Party Requirements:** Built strictly around `urllib.request` and `json`. Runs perfectly out-of-the-box on standard Python 3 execution layers without needing `pip install requests`.
* **Cascade Ordering:** Services are cleared first. This design takes advantage of native PagerDuty behavior:
  1. Deleting a Service automatically drops its child Webhook subscriptions.
  2. Deleting a Service decouples it from Escalation Policies, clearing policy locks so they can be seamlessly deleted right after.
* **Smart Pagination:** Dynamically tracks the PagerDuty pagination metadata loop (`more`/`offset`) to easily process large scale deployments.

---

## Setup & Variables Configuration

1. Place `cleanup.py` and `config.json` inside the same directory workspace.
2. Edit `config.json` to insert your active API credentials:

```json
{
  "api_key": "YOUR_PAGERDUTY_REST_API_KEY",
  "dry_run": true,
  "cleanup_settings": {
    "services": {
      "enabled": true,
      "name_starts_with": "SN:"
    },
    "escalation_policies": {
      "enabled": true,
      "name_starts_with": "SN:"
    }
  }
}

---
**Setup:** edit `config.json` and replace the placeholder values with your own. Keep your real API key out of commits. Run with `dry_run` enabled first.
