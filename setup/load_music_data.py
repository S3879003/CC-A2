import boto3
import json

def load_music_data():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('music')

    with open("a2.json") as json_file:
        data = json.load(json_file)
        songs = data.get('songs', [])

        for song in songs:
            title = song.get('title', '')
            artist = song.get('artist', '')
            year = song.get('year', '')
            web_url = song.get('web_url', '')
            img_url = song.get('img_url', '')

            print("Add song:", title, artist)

            table.put_item(
                Item={
                    'title': title,
                    'artist': artist,
                    'year': year,
                    'web_url': web_url,
                    'img_url': img_url
                }
            )

if __name__ == "__main__":
    load_music_data()
