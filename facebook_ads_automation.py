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
app_id = "Facebook application ID"
app_secret = "facebook app secret token"
access_token = "here is the token of your Facebook application in production mode"
ad_account_id = "act_ADVERTISING_ACCOUNT_ID" #act_+ Necessarily

FacebookAdsApi.init(app_id, app_secret, access_token)


# Function to access Google Drive and download videos
def download_videos_from_drive(drive_link):
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    folder_id = "Here are the folder IDs from Google Drive" 
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
def create_campaign():
    campaign = AdAccount(ad_account_id).create_campaign(
        fields=[AdAccount.Field.name],
        params={
            "name": "My Campaign",
            "objective": "OUTCOME_TRAFFIC",  # Set the campaign goal
            "special_ad_categories": ["NONE"],  # Pass the value NONE as a list
        },
    )
    return campaign


# Function to create a set of declarations
def create_ad_set(campaign_id):
    # Calculate the date and time for the next day at 5 am
    start_time = (datetime.now() + timedelta(days=1)).replace(
        hour=5, minute=0, second=0, microsecond=0
    )

    ad_set = AdAccount(ad_account_id).create_ad_set(
        fields=[AdSet.Field.name],
        params={
            "name": "Hooks {hook_number} + Script {script_number}",
            "campaign_id": campaign_id,
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "LINK_CLICKS",
            "bid_amount": 100,  # Bet amount (in your account currency)
            "daily_budget": 5000,  # Daily budget (in your account currency)
            "targeting": {
                "geo_locations": {"countries": ["GB"]},
                "age_min": 30,
                "age_max": 65,
            },
            "start_time": start_time.strftime(
                "%Y-%m-%dT%H:%M:%S%z"
            ),  # Schedule for the next day at 5 am
            # "end_time": "2024-05-17T05:00:00+0000",  #  Specify an end date if necessary
            "publisher_platforms": ["facebook"],
            "device_platforms": ["mobile", "desktop"],
            "facebook_positions": [
                "feed",
                "video_feeds",
                "instant_article",
            ],  # Specify the required positions
        },
    )
    return ad_set


# Function to create an ad
def create_ad(ad_set_id, video_file):
    video_path = f"./{video_file}"
    thumbnail = f'{video_file.split(".")[0]}.jpg'  # Title of the preview image (first frame of the video)
    ad_creative = AdCreative(parent_id=ad_account_id)
    ad_creative[AdCreative.Field.object_story_spec] = {
        "page_id": "",  # ID of your Facebook page
        "link_data": {
            # "image_hash": "YOUR_IMAGE_HASH",  # Preview image hash
            "link": "Here is your link to the site, people will follow it",  # URL of your website
            "message": "YOUR_PRIMARY_TEXT",  # Main text
            "name": "YOUR_HEADLINE",  # Header
            "description": "YOUR_DESCRIPTION",  # Description
            "call_to_action": {
                "type": "LEARN_MORE",
                "value": {"link": "Here is your link to the site, people will follow it"},
            },  # Call to action
        },
    }
    ad_creative.remote_create()

    ad = Ad(parent_id=ad_account_id)
    ad[Ad.Field.name] = ""
    ad[Ad.Field.adset_id] = ad_set_id
    ad[Ad.Field.creative] = {"creative_id": ad_creative.get_id()}
    ad[Ad.Field.object_story_spec] = ad_creative[AdCreative.Field.object_story_spec]
    ad[Ad.Field.thumbnail_url] = thumbnail
    ad[Ad.Field.video_id] = video_file
    ad[Ad.Field.status] = "ACTIVE"
    ad.remote_create(params={"file": video_path})
    os.remove(video_path)  # Delete video after downloading


# Main function
def main():
    drive_link = "Here is your link to the Google Drive folder"
    videos = download_videos_from_drive(drive_link)
    campaign = create_campaign()
    ad_set = create_ad_set(campaign.get_id())
    for video in videos:
        create_ad(ad_set.get_id(), video)


if __name__ == "__main__":
    main()
