# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "python-dotenv",
#   "pyicloud"
# ]
# ///

import os
import sys
import datetime
from pathlib import Path
from pyicloud import PyiCloudService
from dotenv import load_dotenv

script_dir = Path(__file__).parent
env_path = script_dir / '.env.icloud'

load_dotenv(dotenv_path=env_path)

APPLE_ID = os.getenv('ICLOUD_USERNAME')
PASSWORD = os.getenv('ICLOUD_PASSWORD')

def fetch_reminders(reminders):
    print(f'[{datetime.datetime.now().isoformat()}] Fetching reminders...', file=sys.stderr)

    target_list = next(iter(reminders.lists()), None)
    if target_list is None:
        raise RuntimeError("No reminder lists found")

    result = reminders.list_reminders(
        list_id = target_list.id,
        include_completed=False,
        results_limit=200
    )

    return result

if __name__ == "__main__":
    print(f'[{datetime.datetime.now().isoformat()}] Authenticating...', file=sys.stderr)

    PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
    STATE_DIR = os.path.join(PROJECT_DIR, ".icloud_state")

    os.makedirs(STATE_DIR, exist_ok=True)

    api = PyiCloudService(APPLE_ID, PASSWORD, cookie_directory=STATE_DIR)

    if api.requires_2fa:
        print(f'[{datetime.datetime.now().isoformat()}] 2FA Required. ', file=sys.stderr)
        if sys.stdin.isatty():
            print("Please enter the code sent to your iPhone:", file=sys.stderr)
            code = input()

            result = api.validate_2fa_code(code)
            if not result:
                print("Failed to verify 2FA code", file=sys.stderr)
                sys.exit(1)
        else:
            print(f'[{datetime.datetime.now().isoformat()}] CRITICAL: 2FA required but script is running headlessly. Exiting.', file=sys.stderr)
            sys.exit(1)

    res = fetch_reminders(api.reminders)

    print(f'[{datetime.datetime.now().isoformat()}] Compiling list...', file=sys.stderr)
    if res.reminders:
        print("\n iCLOUD REMINDERS")
        for reminder in res.reminders:
            if reminder.due_date:
                date_str = f" [{reminder.due_date.strftime('%Y-%m-%d %I:%M %p')}]"
            else:
                date_str = ""

            print(f'- {reminder.title}{date_str}')

