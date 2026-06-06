#!/bin/bash

source ~/.config/notion/credentials

NOTION_VERSION="2026-03-11"

# --- Date Calculations --- 
TODAY=$(date +%Y-%m-%d)
TOMORROW=$(date -d "tomorrow" +%Y-%m-%d)

DAY_OF_WEEK=$(date +%u)
DAYS_TO_SUNDAY=$((7 - DAY_OF_WEEK))
THIS_SUNDAY=$(date -d "+$DAYS_TO_SUNDAY days" +%Y-%m-%d)


fetch_tasks() {
  local CATEGORY_NAME="$1"
  local FILTER_JSON="$2"

  local PAYLOAD=$(cat <<EOF
{
  "filter":  $FILTER_JSON
}
EOF
)

  local RESPONSE=$(curl -s -m 10 -X POST "https://api.notion.com/v1/data_sources/$TASKS_DATABASE_ID/query" \
    -H "Authorization: Bearer $TASKS_NOTION_TOKEN" \
    -H "Notion-Version: $NOTION_VERSION" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

  local TASKS=$(echo "$RESPONSE" | jq -r '.results[].properties.Name.title[0].plain_text // empty')

  if [ -n "$TASKS" ]; then
    echo -e "\n$CATEGORY_NAME"
    echo "$TASKS" | sed 's/^/- /'
  fi
}

fetch_calendar() {
  local RESPONSE=$(curl -sL "${GCAL_API_URL}?token=${GCAL_TOKEN}")
    
  local TODAY_EVENTS=$(echo "$RESPONSE" | jq -r '.today | join("\n")')
  local WEEK_EVENTS=$(echo "$RESPONSE" | jq -r '.thisWeek | join("\n")')

  if [ -n "$TODAY_EVENTS" ]; then
    echo -e "\n🗓️ TODAY'S SCHEDULE"
    echo "$TODAY_EVENTS"
  fi

  if [ -n "$WEEK_EVENTS" ]; then
    echo -e "\n🗓️ LATER THIS WEEK (CALENDAR)"
    echo "$WEEK_EVENTS"
  fi
}

# --- Filters ---

OVERDUE_FILTER=$(cat <<EOF
{
  "and": [
    { "property": "Status", "status": { "does_not_equal": "Done" } },
    { "property": "Due Date", "date": { "before": "$TODAY" } }
  ]
}
EOF
)

TODAY_FILTER=$(cat <<EOF
{
  "and": [
    { "property": "Status", "status": { "does_not_equal": "Done" } },
    { "property": "Due Date", "date": { "equals": "$TODAY" } }
  ]
}
EOF
)

WEEK_FILTER=$(cat <<EOF
{
  "and": [
    { "property": "Status", "status": { "does_not_equal": "Done" } },
    { "property": "Due Date", "date": { "on_or_after": "$TOMORROW" } },
    { "property": "Due Date", "date": { "on_or_before": "$THIS_SUNDAY"} }
  ]
}
EOF
)

SPRINT_FILTER=$(cat <<EOF
{
  "and": [
    { "property": "Status", "status": { "does_not_equal": "Done" } },
    { "property": "Status", "status": { "does_not_equal": "Backlog" } },
    {
      "or": [
        { "property": "Due Date", "date": { "is_empty": true } },
        { "property": "Due Date", "date": { "after": "$THIS_SUNDAY" } }
      ]
    }
  ]
}
EOF
)
# --- Execution ---

LOG_DIR="$HOME/workspace/scripts/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/reminders_log.txt"

# Capture all output into a single variable
MESSAGE_CONTENT=$(
    fetch_calendar

    uv run "$HOME/workspace/scripts/fetch_icloud_reminders.py" 2>> "$LOG_FILE"

    fetch_tasks "🚨 OVERDUE" "$OVERDUE_FILTER"
    fetch_tasks "📍 DUE TODAY" "$TODAY_FILTER"
    fetch_tasks "📅 LATER THIS WEEK" "$WEEK_FILTER"
    fetch_tasks "🏃 CURRENT SPRINT" "$SPRINT_FILTER"
)

# Strip whitespace to check if the message is actually empty
if [ -n "${MESSAGE_CONTENT// /}" ]; then
    
    # Use jq to safely escape the string into a valid JSON payload
    JSON_PAYLOAD=$(jq -n --arg content "$MESSAGE_CONTENT" '{content: $content}')

    # Send the payload to the Discord Webhook
    curl -s -X POST -H "Content-Type: application/json" -d "$JSON_PAYLOAD" "$DISCORD_WEBHOOK_URL"
fi   
