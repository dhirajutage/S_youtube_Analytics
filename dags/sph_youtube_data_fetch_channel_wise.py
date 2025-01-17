from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import os
import json
import boto3
from googleapiclient.discovery import build
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta

# DAG configuration
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'retries': 1,
}

dag = DAG(
    'sph_youtube_data_fetch_channel_wise',
    default_args=default_args,
    description='A DAG to fetch YouTube data for each channel and save to MinIO',
    schedule_interval='@daily',
)

# Calculate the date 12 months ago from today
twelve_months_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")

# YouTube API key
api_key = 'AIzaSyCxkJNHWe5hUSu9VKxLjDyrdkAuLsGwqcA'

# Channel IDs
channel_ids = {
    'The Straits Times': 'UC4p_I9eiRewn2KoU-nawrDg',
    'The Business Times': 'UC0GP1HDhGZTLih7B89z_cTg',
    'zaobaosg': 'UCrbQxu0YkoVWu2dw5b1MzNg',
    'Tamil Murasu': 'UCs0xZ60FSNxFxHPVFFsXNTA',
    'Berita Harian': 'UC_WgSFSkn7112rmJQcHSUIQ'
}

# MinIO bucket details
bucket_name = 'landing'
minio_endpoint = 'http://host.docker.internal:9000'
minio_access_key = 'admin'
minio_secret_key = 'password'

# MinIO client
minio_client = boto3.client(
    's3',
    endpoint_url=minio_endpoint,
    aws_access_key_id=minio_access_key,
    aws_secret_access_key=minio_secret_key
)

# Build YouTube API client
youtube = build('youtube', 'v3', developerKey=api_key)

def fetch_channel_stats(channel_id, channel_name):
    request = youtube.channels().list(
        part='snippet,contentDetails,statistics',
        id=channel_id
    )
    response = request.execute()

    item = response['items'][0]
    data = {
        "channelName": item['snippet']['title'],
        "subscribers": item['statistics']['subscriberCount'],
        "views": item['statistics']['viewCount'],
        "totalVideos": item['statistics']['videoCount'],
        "playlistId": item['contentDetails']['relatedPlaylists']['uploads']
    }

    return data



def fetch_video_ids(playlist_id):
    video_ids = []
    request = youtube.playlistItems().list(
        part='contentDetails',
        playlistId=playlist_id,
        maxResults=50
    )
    response = request.execute()

    for item in response['items']:
        video_ids.append(item['contentDetails']['videoId'])

    next_page_token = response.get('nextPageToken')
    while next_page_token:
        request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])

        next_page_token = response.get('nextPageToken')

    return video_ids

def fetch_video_details(video_ids):
    all_video_info = []

    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(video_ids[i:i + 50])
        )
        response = request.execute()

        for video in response['items']:
            published_at = video['snippet']['publishedAt']
            # Filter to include only videos published in the last 12 months
            if published_at >= twelve_months_ago:
                video_info = {
                    'videoId': video['id'],
                    'channelTitle': video['snippet']['channelTitle'],
                    'title': video['snippet']['title'],
                    'description': video['snippet']['description'],
                    'publishedAt': published_at,
                    'viewCount': video['statistics'].get('viewCount'),
                    'likeCount': video['statistics'].get('likeCount'),
                    'commentCount': video['statistics'].get('commentCount'),
                    'duration': video['contentDetails'].get('duration', '0'),
                    'definition': video['contentDetails']['definition']
                }
                all_video_info.append(video_info)

    return all_video_info

def process_channel(channel_id, channel_name):
    # Fetch channel stats
    channel_data = fetch_channel_stats(channel_id, channel_name)

    # Fetch video IDs
    video_ids = fetch_video_ids(channel_data['playlistId'])

    # Fetch video details for the last 12 months
    video_details = fetch_video_details(video_ids)

    # Add video details to channel data
    channel_data['videos'] = video_details

    # Save data to MinIO
    folder_name = f"{channel_name.replace(' ', '_')}"
    file_name = f"{channel_name.replace(' ', '_')}_raw_data.json"
    save_to_minio(channel_data, folder_name, file_name)

def save_to_minio(data, folder_name, file_name):
    try:
        json_data = json.dumps(data)
        object_key = f"{folder_name}/{file_name}"
        minio_client.put_object(Bucket=bucket_name, Key=object_key, Body=json_data)
        print(f"Raw data saved to MinIO as {object_key}")
    except Exception as e:
        print(f"Failed to save data to MinIO. Error: {e}")

# Create tasks for each channel
process_tasks = []

for channel_name, channel_id in channel_ids.items():
    task = PythonOperator(
        task_id=f'process_{channel_name.replace(" ", "_")}',
        python_callable=process_channel,
        op_args=[channel_id, channel_name],
        dag=dag,
    )
    process_tasks.append(task)  # Add the task to the list

# Create the TriggerDagRunOperator task
trigger_processing_dag = TriggerDagRunOperator(
    task_id='trigger_data_processing_dag',
    trigger_dag_id='sph_youtube_data_processing', 
    dag=dag,
)
######## Trigger processing DAG  ###################################

# Set up the dependency: all process_* tasks must complete before trigger_processing_dag is executed
for task in process_tasks:
    task >> trigger_processing_dag
