import boto3
import json
import requests
import os

def download_images(json_file):
    with open(json_file) as f:
        data = json.load(f)
        songs = data.get('songs', [])

        for song in songs:
            img_url = song.get('img_url', '')
            if img_url:
                download_image(img_url)

def download_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        # Extract the filename from the URL
        filename = url.split('/')[-1]
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded image: {filename}")
        upload_to_s3(filename)
    else:
        print(f"Failed to download image from URL: {url}")

def upload_to_s3(filename):
    s3 = boto3.client('s3')
    bucket_name = 'a2-bucket' 

    try:
        s3.upload_file(filename, bucket_name, filename)
        print(f"Uploaded image '{filename}' to S3 bucket '{bucket_name}'")
    except Exception as e:
        print(f"Failed to upload image '{filename}' to S3 bucket '{bucket_name}': {str(e)}")

    # Clean up: delete the local file after uploading
    os.remove(filename)
    print(f"Deleted local image file: {filename}")

if __name__ == "__main__":
    download_images('a2.json')
