#!/usr/bin/env python3
import requests
from requests.auth import HTTPBasicAuth
import json
import httpx
from httpx import DigestAuth

# Configuration
TVH_HOST = "172.22.2.103"
TVH_PORT = "9981"
USERNAME = "admin"
PASSWORD = "1234"

# News broadcast schedule
NEWS_SCHEDULE = [
    {
        "title": "7AM Breakfast Show",
        "start_time": "06:50",
        "stop_time": "08:10"
    },
    {
        "title": "1PM News",
        "start_time": "12:50",
        "stop_time": "13:40"
    },
    {
        "title": "7PM News", 
        "start_time": "18:50",
        "stop_time": "19:50"
    },
    {
        "title": "9PM News",
        "start_time": "20:50", 
        "stop_time": "22:20"
    }
]

def create_autorec(channel, name, title, start_time, stop_time, weekdays="1111111"):
    """Create an autorec entry"""
    
    url = f"http://{TVH_HOST}:{TVH_PORT}/api/dvr/autorec/create"
    
    data = {
        "name": name,
        "title": title,
        "channel": channel,
        "enabled": 1,
        "start": start_time,
        "stop": stop_time, 
        "weekdays": [1,2,3,4,5,6,7],
        "config_name": "oxygene"
    }
    
    try:
        # Add authentication if needed
        auth = DigestAuth(USERNAME, PASSWORD)
        # response = httpx.post(url, json=data, auth=auth)
        response = httpx.post(url, json= { "conf":  data }, auth=auth)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✓ Created autorec: {title} on {channel}")
                return True
            else:
                print(f"✗ Failed to create {title}: {result.get('text', 'Unknown error')}")
                return False
        else:
            print(response.text)
            print(f"✗ HTTP Error {response.status_code} for {title}")
            return False
            
    except requests.RequestException as e:
        print(f"✗ Network error creating {title}: {e}")
        return False

def get_channels():
    """Get list of available channels"""
    try:
        url = f"http://{TVH_HOST}:{TVH_PORT}/api/channel/list"
        auth = DigestAuth(USERNAME, PASSWORD)
        response = httpx.get(url, auth=auth)
        if response.status_code == 200:
            channels = response.json()
            return channels.get("entries", [])
        else:
            print(f"Failed to get channels: HTTP {response.status_code}")
            return []
    except httpx.RequestError as e:
        print(f"Request failed: {e}")
        return []

def main():
    print("TVHeadend News Autorec Creator")
    print("=" * 40)
    
    # Get available channels
    print("Getting channel list...")
    channels = get_channels()
    tv_channels = [
        # "PANG-K24",
        # "PANG-KBC1",
        # "PANG-KTN HOME",
        # "PANG-TV47",
    
        "Signet TV47",
        "Signet NTV",
        "Signet KTN TV",
        "Signet K24 TV",
        "Signet Citizen TV",
        "Signet KBC1"
    ]

    radio_channels = [
        "PANG-SPICE FM",
        "PANG-GHETTO RADIO",
    ]
    
    if not channels:
        print("No channels found or connection failed!")
        return
    
    print(f"Found {len(channels)} channels")
    
    # Get channel selection
    channel_name = input(f"\nEnter channel name (or number 1-{min(10, len(channels))}): ").strip()
    channel_uuid = ""
    
    # Handle numeric selection
    try:
        channel_num = int(channel_name)
        if 1 <= channel_num <= min(10, len(channels)):
            channel_name = channels[channel_num - 1]
        else:
            print("Invalid channel number")
            return
    except ValueError:
        # User entered channel name directly
        for ch in channels:
            if ch.get("name", "").lower() == channel_name.lower():
                channel_uuid = ch["uuid"]
    
    # Get weekdays selection
    print("\nWeekdays selection:")
    print("  1. Every day (Mon-Sun)")
    print("  2. Weekdays only (Mon-Fri)")  
    print("  3. Custom")
    
    weekday_choice = input("Choose (1-3): ").strip()
    
    if weekday_choice == "1":
        weekdays = "1111111"  # All days
        weekday_desc = "every day"
    elif weekday_choice == "2": 
        weekdays = "1111100"  # Mon-Fri
        weekday_desc = "weekdays only"
    elif weekday_choice == "3":
        print("Enter 1 for record, 0 for skip:")
        mon = input("Monday (1/0): ").strip()
        tue = input("Tuesday (1/0): ").strip()
        wed = input("Wednesday (1/0): ").strip()
        thu = input("Thursday (1/0): ").strip()
        fri = input("Friday (1/0): ").strip()
        sat = input("Saturday (1/0): ").strip()
        sun = input("Sunday (1/0): ").strip()
        weekdays = f"{mon}{tue}{wed}{thu}{fri}{sat}{sun}"
        weekday_desc = "custom schedule"
    else:
        print("Invalid choice")
        return
    
    # Create autorecs
    print(f"\nCreating autorecs for {channel_name} ({weekday_desc})...")
    print("-" * 50)
    
    success_count = 0
    for schedule in NEWS_SCHEDULE:
        if create_autorec(
            channel=channel_uuid,
            # channel=channel_name,
            name=f"{channel_name} _ {schedule["title"]}",
            title=schedule["title"],
            start_time=schedule["start_time"],
            stop_time=schedule["stop_time"],
            weekdays=weekdays
        ):
            success_count += 1
    
    print("-" * 50)
    print(f"Successfully created {success_count}/{len(NEWS_SCHEDULE)} autorecs")
    
    if success_count > 0:
        print(f"\nNews recordings will now happen:")
        for schedule in NEWS_SCHEDULE:
            print(f"  • {schedule['title']}: {schedule['start_time']}-{schedule['stop_time']}")
        print(f"  • Channel: {channel_name}")
        print(f"  • Schedule: {weekday_desc}")

if __name__ == "__main__":
    main()