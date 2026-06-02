# /// script
# requires-python = ">=3.14"
# dependencies = [
#       "requests",
#       "python-dotenv"
#
# ]
# ///

import os
import json
import requests
import sys
from pathlib import Path
from dotenv import load_dotenv


script_dir = Path(__file__).parent
env_path = script_dir / '.env.social'

load_dotenv(dotenv_path=env_path)

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
API_KEY = os.getenv('GEMINI_API_KEY')

if not DISCORD_WEBHOOK_URL or not API_KEY:
    print(f'Error: Missing variables: check {env_path}')
    sys.exit(1)

LLM_VERSION = 'gemini-3-flash-preview'
LLM_URL = f'https://generativelanguage.googleapis.com/v1beta/models/{LLM_VERSION}:generateContent?key={API_KEY}' 
PROMPT_TEXT = ''' 
You are an AI assistant designed to prompt the user to post on social media. Follow these exact steps to generate the user's daily assignment: 
    1. Randomly select exactly one platform from this list: Facebook, Instagram, LinkedIn, Snapchat. 
    2. Based on the selected platform, randomly select one post category from the platform's corresponding list below. 
    3. Generate a highly specific, actionable post idea that fits the selected category. Ensure the specific subject matter is randomized and unique every time so the user never gets the exact same prompt twice.
Platform Guidelines & Categories: 
    - Facebook: Categories: [Community Discussion, Minor Life Update, Relatable Observation, Humor] 
    - Instagram: Categories: [Current Environment/Workspace, Hobby Showcase, Daily Habit/Routine, 'Story-Time' Photo Dump] 
    - LinkedIn: Categories: [Recent Lesson Learned, Industry Trend Question, Productivity/Workflow Tip, Tool/Concept Appreciation] 
    - Snapchat: Categories: [Current View/POV, Quick Rant/Thought of the Day, Meal/Beverage Snapshot, Interactive Friend Poll] 
Output your response in the following format exactly, with no additional conversational text: 
    Time to post on [Platform]! Topic: [Category] Your Assignment: [1-2 sentences detailing exactly what the user should capture or write right now]
'''

def generate_social_prompt():
    ''' Calls the LLM API to generate a randomize social media assignment '''
    payload = {
        'contents': [{'parts': [{'text': PROMPT_TEXT}]}],
        'generationConfig': {
            'temperature': 0.9
        }
    }

    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(LLM_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text'].strip()
    except requests.exceptions.RequestException as e:
        print(f'LLM API Call Failed: {e}')
        sys.exit(1)


def send_to_discord(content):
    ''' Pushes the generated text to the Discord webhook. '''
    payload = {
        'content': f'**Daily Social Media Assignment**\n\n{content}'
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(str(DISCORD_WEBHOOK_URL), headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        print("Successfully dispatched to Discord.")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            print(f"Discord Rate Limited. Retry after: {response.json().get('retry_after', 'unknown')} seconds.")
        else:
            print(f"Discord Webhook Failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("Generating assignment...")
    assignment = generate_social_prompt()
    send_to_discord(assignment)
