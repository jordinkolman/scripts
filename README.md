# Scripts 
## 1. Notion Daily Task Fetcher - `notion_daily.sh`
- Fetches Calendar events from Google calendar for the current day and week
- Uses iCloud Reminder Fetcher to fetch list of incomplete reminders
- Fetches tasks from Notion database and 
- Sends a Discord message in categories: 
  - Calender Events Today
  - Calender Events This Week
  - iCloud Reminders
  - Overdue Tasks
  - Tasks Due Today
  - Tasks Due This Week
  - Tasks Due This Sprint

## 2. Social Media Post Prompt Generator - `social_automation.py`
- Makes a call to a specified LLM to generate a random prompt for a social media post based on specified platform and category parameters

## 3. iCloud Reminder Fetcher - `fetch_icloud_reminders.py`
- Fetches incomplete reminders from iCloud and outputs as strings
- Designed to be called by Notion Daily Task Fetcher to be included in final output to Discord
