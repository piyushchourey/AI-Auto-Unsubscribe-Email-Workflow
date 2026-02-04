# Database Features - Blocklist Tracking

## Overview

The Unsubscribe Email Workflow now includes comprehensive database tracking of all blocklist actions. Every email processed (whether from webhook or IMAP worker) is logged to a SQLite database for future reference, auditing, and export.

## What's Tracked

For each email processed, the system records:

- **Email Address**: The sender's email that was processed
- **Intent Detection Results**:
  - Whether unsubscribe intent was detected (Yes/No)
  - Confidence level (high/medium/low)
  - LLM reasoning for the decision
- **Brevo API Results**:
  - Whether the Brevo API call was successful
  - Action taken (created/updated/failed)
  - Brevo response message
- **Email Metadata**:
  - Email subject
  - Email snippet (first 200 characters)
- **Source**: How the email was processed (webhook/worker/manual)
- **Timestamp**: When the action occurred

## Database Location

- **Database File**: `data/unsubscribe_history.db`
- **Database Type**: SQLite (no setup required!)
- **Auto-Created**: The database and tables are automatically created on first run

## API Endpoints

### 1. Get Statistics

```bash
GET /blocklist/stats
```

**Returns**:
```json
{
  "success": true,
  "stats": {
    "total_processed": 25,
    "intent_detected_count": 15,
    "successfully_blocklisted": 14,
    "failed_blocklist": 1,
    "no_intent_detected": 10,
    "source_breakdown": {
      "webhook": 10,
      "worker": 15
    }
  }
}
```

### 2. Get All Blocklisted Emails

```bash
GET /blocklist/all?successful_only=true
```

**Query Parameters**:
- `successful_only` (bool, default: true): Only return successfully blocklisted emails

**Returns**:
```json
{
  "success": true,
  "count": 14,
  "emails": [
    {
      "id": 1,
      "email": "user@example.com",
      "intent_detected": true,
      "intent_confidence": "high",
      "brevo_success": true,
      "brevo_action": "updated",
      "email_subject": "Unsubscribe Request",
      "source": "webhook",
      "created_at": "2026-02-03T12:30:45"
    },
    ...
  ]
}
```

### 3. Search by Email

```bash
GET /blocklist/search/{email}
```

**Example**:
```bash
curl http://localhost:8000/blocklist/search/user@example.com
```

### 4. Get Recent Logs

```bash
GET /blocklist/recent?limit=50
```

**Query Parameters**:
- `limit` (int, default: 50, max: 500): Number of recent logs to return

### 5. Export to CSV

```bash
GET /blocklist/export?successful_only=true
```

**Downloads CSV file** with columns:
- id, email, intent_detected, intent_confidence
- brevo_success, brevo_action, email_subject
- source, created_at

**Example**:
```bash
# Download CSV export
curl -o blocklist.csv http://localhost:8000/blocklist/export
```

## Streamlit UI Integration

The new **Blocklist** tab in the Streamlit UI provides:

### Statistics Dashboard
- Total processed emails
- Intent detection count
- Successfully blocklisted count
- Failed attempts
- Breakdown by source (webhook vs worker)

### Recent Entries Table
- Interactive table showing recent blocklist entries
- Configurable limit (10, 25, 50, 100 entries)
- Visual indicators (✅/❌) for status
- Formatted timestamps

### Export Functionality
- One-click export to CSV
- Download button for immediate download
- Timestamped filenames

### Search Feature
- Search by email address
- Returns all matching entries with full details
- JSON display of results

## Use Cases

### 1. Compliance & Auditing
Track all unsubscribe requests for compliance with email regulations (GDPR, CAN-SPAM, etc.)

```bash
# Get all processed emails for audit
curl http://localhost:8000/blocklist/all?successful_only=false
```

### 2. Reporting
Generate monthly reports on unsubscribe requests:

```bash
# Export to CSV for analysis
curl -o monthly_report.csv http://localhost:8000/blocklist/export
```

### 3. Troubleshooting
Check if a specific user was processed:

```bash
# Search for specific email
curl http://localhost:8000/blocklist/search/user@example.com
```

### 4. Analytics
Understanding unsubscribe patterns:

```python
import requests
import pandas as pd

# Get all data
response = requests.get("http://localhost:8000/blocklist/all?successful_only=false")
data = response.json()
emails = data['emails']

# Convert to DataFrame for analysis
df = pd.DataFrame(emails)

# Analyze by confidence level
print(df.groupby('intent_confidence').size())

# Analyze by source
print(df.groupby('source').size())
```

## Example Workflow

1. **Email arrives** (via webhook or worker)
2. **Intent detection** runs (LLM analyzes the message)
3. **Brevo API** called (if intent detected)
4. **Database logs** the complete action
5. **Admin can view** in Streamlit UI or via API
6. **Export to CSV** for reporting/analysis

## Testing the Database

### View Statistics
```bash
curl http://localhost:8000/blocklist/stats
```

### View Recent Entries
```bash
curl http://localhost:8000/blocklist/recent?limit=10
```

### Search for Email
```bash
curl http://localhost:8000/blocklist/search/test@example.com
```

### Export Data
```bash
curl -o export.csv http://localhost:8000/blocklist/export
```

## Database Schema

**Table**: `unsubscribe_logs`

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| email | String | Email address processed |
| intent_detected | Boolean | Was unsubscribe intent detected? |
| intent_confidence | String | high/medium/low |
| intent_reasoning | Text | LLM's explanation |
| brevo_success | Boolean | Was Brevo API call successful? |
| brevo_action | String | created/updated/failed |
| brevo_message | Text | Brevo API response |
| email_subject | String | Email subject line |
| email_snippet | Text | First 200 chars of message |
| source | String | webhook/worker/manual |
| created_at | DateTime | Timestamp of action |

## Benefits

✅ **Compliance**: Keep records of all unsubscribe requests
✅ **Audit Trail**: Complete history of actions taken
✅ **Analytics**: Understand unsubscribe patterns
✅ **Troubleshooting**: Verify if emails were processed
✅ **Reporting**: Easy export to CSV for analysis
✅ **No Setup Required**: SQLite works out of the box
✅ **Lightweight**: File-based database, no server needed

## Future Enhancements

Potential additions:
- Email templates/content analysis
- Bounce tracking integration
- Dashboard charts and graphs
- Scheduled export reports
- Integration with other systems

## Support

For questions or issues with the database features, check:
1. Database file exists: `data/unsubscribe_history.db`
2. API endpoints respond correctly
3. Streamlit Blocklist tab loads
4. Check API logs for database errors
