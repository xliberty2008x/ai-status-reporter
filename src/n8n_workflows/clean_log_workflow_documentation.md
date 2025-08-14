# Clean Log Previous Month - n8n Workflow Documentation

## Overview
This n8n workflow implements the monthly data retention cleanup policy as defined in the Python implementation. It automatically deletes records older than the previous calendar month from the Project Status Change Log database.

## Workflow Status: ✅ PRODUCTION READY
- **Tested:** August 13, 2025
- **Test Results:** Successfully deleted 19 old records, kept 15 recent records
- **Performance:** Accurate date calculations and proper batch processing

## Schedule Configuration
- **Runs:** Daily at 23:00 UTC
- **Cron Expression:** `0 23 * * *`
- **Actual Execution:** Only on the last day of each month
- **Workaround Note:** Uses daily trigger with last-day check since n8n doesn't support "L" in cron

## Workflow Components

### 1. Schedule Trigger - Daily
- **Type:** scheduleTrigger
- **Schedule:** Daily at 23:00 UTC
- **Purpose:** Triggers workflow daily for last-day check

### 2. Check If Last Day of Month
- **Type:** Code node (JavaScript)
- **Logic:** Checks if tomorrow is the 1st (meaning today is last day)
```javascript
const tomorrow = new Date(today);
tomorrow.setDate(today.getDate() + 1);
const isLastDayOfMonth = tomorrow.getDate() === 1;
```
- **Output:** Boolean flag and execution metadata

### 3. Is Last Day?
- **Type:** IF node
- **Condition:** `isLastDayOfMonth === true`
- **True Path:** Proceeds to cleanup
- **False Path:** Workflow ends (no action)

### 4. Calculate Cutoff Date
- **Type:** Code node
- **Calculates:** First day of previous month
- **Logic:** 
  - January → December 1st of previous year
  - Other months → Previous month's 1st day
- **Output:** ISO date for Notion API filtering

### 5. Get Records to Delete
- **Type:** Notion node
- **Operation:** Get all database pages
- **Filter:** `Date before cutoffDate`
- **Database ID:** d94056721a9b4a4fa836743010fafec7
- **Returns:** All records older than cutoff

### 6. Prepare Deletion Summary
- **Type:** Code node
- **Purpose:** Process and summarize records for deletion
- **Important:** Uses `property_` prefix for Notion fields
```javascript
const date = record.property_date?.start || null;
const projectName = record.property_project_name || 'Unknown';
const team = record.property_team || 'Unknown';
```
- **Output:** Statistics by team, platform, month, and date range

### 7. Check If Records Found
- **Type:** IF node
- **Condition:** `recordsFound === true`
- **True Path:** Proceed with deletion
- **False Path:** Send "no records" message

### 8. Deletion Branch (If Records Found)

#### Split Into Batches
- **Type:** splitInBatches
- **Batch Size:** 10 records
- **Purpose:** Prevent API rate limit issues

#### Archive Pages
- **Type:** Notion node
- **Operation:** Archive (soft delete)
- **Page ID:** From deletion list
- **Note:** Archived pages can be restored if needed

#### Wait Between Batches
- **Type:** Wait node
- **Duration:** 1 second
- **Purpose:** Rate limiting compliance

#### Generate Cleanup Report
- **Type:** Code node
- **Creates:** Final statistics report
- **Includes:** Total deleted, breakdowns, date ranges

#### Send Slack Report
- **Type:** Slack node
- **Channel:** project-status-update
- **Format:** Detailed cleanup summary with emojis

### 9. No Records Branch

#### Send No Records Message
- **Type:** Slack node
- **Message:** Informational - no deletion needed
- **Shows:** Current cutoff date for reference

## Data Flow
```
Daily Trigger → Check Last Day → IF Last Day
                                    ↓
                              Calculate Cutoff
                                    ↓
                            Get Records to Delete
                                    ↓
                          Prepare Deletion Summary
                                    ↓
                          Check If Records Found
                               ↙        ↘
                    Delete & Report    No Records Message
```

## Testing the Workflow

### Generate Test Data
Use the provided test data generator to create mockup records:

```bash
python src/test_cleanup_mockup.py
```

This script will:
1. Generate ~35 records across 4 time periods:
   - Current month (5-7 records) - KEEP
   - Previous month (8-10 records) - KEEP
   - Two months ago (10-12 records) - DELETE
   - Three months ago (8-10 records) - DELETE

2. Upload records to Notion with proper tags for tracking

3. Create summary reports showing expected behavior

### Manual Testing Steps

1. **Prepare Test Environment:**
   ```bash
   cd /path/to/project
   python src/test_cleanup_mockup.py
   ```

2. **Modify Workflow for Testing:**
   - Temporarily set `isLastDayOfMonth` to `true` in the check node
   - Or wait for actual last day of month

3. **Execute Workflow:**
   - Run manually in n8n
   - Monitor execution for each node

4. **Verify Results:**
   - Check Slack for cleanup report
   - Verify correct record counts
   - Confirm date ranges match expectations
   - Check Notion for archived records

### Expected Test Results
Based on the test data generator:
- **Records to Delete:** All from May and June
- **Records to Keep:** All from July and August
- **Cutoff Date:** First day of previous month
- **Report:** Detailed breakdown by team/platform

## Configuration Requirements

### Notion Configuration
- **API Key:** Required in credentials
- **Database Access:** Read and write permissions
- **Database ID:** d94056721a9b4a4fa836743010fafec7

### Slack Configuration
- **OAuth2 Credentials:** "Vira Bot" 
- **Channel ID:** C09111P5JN6 (project-status-update)
- **Permissions:** Post messages to channel

## Retention Policy Details

### What Gets Deleted
- Records older than the first day of the previous month
- Example (running on August 31):
  - Cutoff: July 1
  - Delete: Everything before July 1
  - Keep: July and August records

### Deletion Method
- **Soft Delete:** Records are archived in Notion
- **Reversible:** Archived pages can be restored
- **Batch Processing:** 10 records at a time

## Monitoring & Maintenance

### Daily Execution
- Workflow runs daily but only acts on last day
- Minimal overhead on non-execution days
- Early exit prevents unnecessary API calls

### Monthly Verification
- Check Slack reports for successful execution
- Verify record counts match expectations
- Monitor for any error messages

### Troubleshooting

**Issue:** Workflow not deleting records
- Check if today is actually the last day
- Verify cutoff date calculation
- Ensure Notion filter is working

**Issue:** API rate limits
- Reduce batch size if needed
- Increase wait time between batches

**Issue:** Wrong records deleted
- Verify timezone handling
- Check date format in Notion
- Review cutoff date calculation

## Performance Metrics

### Test Run Results (August 13, 2025)
- **Total Records Processed:** 19
- **Execution Time:** ~2 minutes
- **Batches Processed:** 2
- **Success Rate:** 100%
- **Date Range Deleted:** May 12 - June 27, 2025

### Resource Usage
- **API Calls:** ~25 (fetch + archive operations)
- **Memory:** Minimal (batch processing)
- **Network:** Light (10 records per batch)

## Best Practices

1. **Testing:** Always test with mockup data first
2. **Monitoring:** Check Slack reports monthly
3. **Backup:** Consider exporting data before large cleanups
4. **Documentation:** Update this doc with any modifications

## Related Files
- **Workflow JSON:** `/src/n8n_workflows/clean_log_previous_month.json`
- **Test Generator:** `/src/test_cleanup_mockup.py`
- **Python Implementation:** `/src/retention_manager.py`
- **Main Documentation:** `/Claude.md`

---
*Documentation created after successful validation on August 13, 2025*
