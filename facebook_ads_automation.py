import math
import os
from datetime import datetime, timedelta
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.ad import Ad
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Initialize Facebook Ads API
app_id = ""
app_secret = ""
access_token = ""
ad_account_id = ""

FacebookAdsApi.init(app_id, app_secret, access_token, api_version='v19.0')

# Function to access Google Drive and download videos
def download_videos_from_drive(folder_id):
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    file_list = drive.ListFile(
        {"q": f"'{folder_id}' in parents and trashed=false"}
    ).GetList()
    videos = []
    for file in file_list:
        if file["mimeType"] == "video/mp4":
            file.GetContentFile(file["title"])
            videos.append(file["title"])
    return videos

# Function for creating a campaign
def create_campaign(name):
    campaign = AdAccount(ad_account_id).create_campaign(
        fields=[AdAccount.Field.id],  # изменение поля на 'id'
        params={
            "name": name, 
            "objective": "OUTCOME_TRAFFIC",
            "special_ad_categories": ["NONE"],
        },
    )
    return campaign.get_id(), campaign  # возвращаем только id кампании

# Function to create a set of ads
def create_ad_sets(campaign_id, folder_name, videos):
    num_ads_per_set = 5
    num_sets = math.ceil(len(videos) / num_ads_per_set)
    start_time = (datetime.now() + timedelta(days=1)).replace(
        hour=5, minute=0, second=0, microsecond=0
    )
    ad_sets = []
    for i in range(num_sets):
        ad_set_name = f"{folder_name} - Ad Set {i+1}"
        ad_set = AdAccount(ad_account_id).create_ad_set(
            fields=[AdSet.Field.name],
            params={
                "name": ad_set_name,
                "campaign_id": campaign_id,
                "billing_event": "IMPRESSIONS",
                "optimization_goal": "LINK_CLICKS",
                "bid_amount": 100,
                "daily_budget": 5000,
                "targeting": {
                    "geo_locations": {"countries": ["GB"]},
                    "age_min": 30,
                    "age_max": 65,
                },
                "start_time": start_time.strftime(
                    "%Y-%m-%dT%H:%M:%S%z"
                ),
                "publisher_platforms": ["facebook"],
                "device_platforms": ["mobile", "desktop"],
                "facebook_positions": [
                    "feed",
                    "video_feeds",
                    "instant_article",
                ],
            },
        )
        ad_sets.append(ad_set)
    return ad_sets

# Function to create an ad
def create_ad(ad_set_id, video_file):
    video_path = f"./{video_file}"
    thumbnail = f'{video_file.split(".")[0]}.jpg'
    ad_creative = AdCreative(parent_id=ad_account_id)
    ad_creative[AdCreative.Field.object_story_spec] = {
        "page_id": "",
        "link_data": {
            "link": "",
            "message": "YOUR_PRIMARY_TEXT",
            "name": "YOUR_HEADLINE",
            "description": "YOUR_DESCRIPTION",
            "call_to_action": {
                "type": "LEARN_MORE",
                "value": {"link": ""},
            },
        },
    }
    ad_creative.remote_create()

    ad = Ad(parent_id=ad_account_id)
    ad[Ad.Field.name] = "EMS Slippers Hooks Creative Sandbox"
    ad[Ad.Field.adset_id] = ad_set_id
    ad[Ad.Field.creative] = {"creative_id": ad_creative.get_id()}
    ad[Ad.Field.object_story_spec] = ad_creative[AdCreative.Field.object_story_spec]
    ad[Ad.Field.thumbnail_url] = thumbnail
    ad[Ad.Field.video_id] = video_file
    ad[Ad.Field.status] = "PAUSED"  
    ad.remote_create(params={"file": video_path})
    os.remove(video_path)

# Main function
def main():
    drive_links = {
        # "Campaign 1": "",
        "Campaign 2": "",
    }
    for campaign_name, drive_link in drive_links.items():
        print("Campaign:", campaign_name)
        print("Google Drive Folder ID:", drive_link)
        videos = download_videos_from_drive(drive_link)
        campaign_id, campaign = create_campaign(campaign_name)
        ad_sets = create_ad_sets(campaign_id, campaign_name, videos)
        for i, video in enumerate(videos):
            ad_set = ad_sets[i // 5]  # 5 ads per ad set
            create_ad(ad_set.get_id(), video)

if __name__ == "__main__":
    main()