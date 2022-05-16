import os
from pathlib import Path
from dotenv import load_dotenv
import slack
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
import requests

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
app = Flask(__name__)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']

slack_event_adapter = SlackEventAdapter(os.environ['SIGN_IN_SECRET'], '/slack/events', app)


@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    if BOT_ID != user_id:
        print(channel_id, text)


@app.route('/getRecommendation', methods=['POST'])
def get_recommendation():
    data = request.form
    genre = data.get('text')
    channel_id = data.get('channel_id')
    user_name = data.get('user_name')
    print(data)
    response = requests.get("https://gospotty.herokuapp.com/api/recommendations")
    return_data = response.json().get('data').get('items')
    client.chat_postMessage(channel=channel_id, blocks=get_message_blocks(return_data, user_name))
    return Response(), 200


def get_message_blocks(items, user):
    blocks = [{
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f'Hey {user}, see the recommendations below'
        }
    }]
    for item in items:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": item.get('title')
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": item.get('title')
                },
                "value": "click_me_123",
                "url": item.get('previewUrl'),
                "action_id": "button-action"
            }
        })
    return blocks


@app.route('/login', methods=['POST'])
def login():
    data = request.form
    channel_id = data.get('channel_id')
    client.chat_postMessage(channel=channel_id, blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Hello, welcome to the GoSpotty App. To continue please login."
            }
        },
        {
            "type": "image",
            "image_url": "https://drive.google.com/uc?export=view&id=1GKQ_eSKvtbhOkvd_5jD0ynyIrGg4NcDB",
            "alt_text": "marg"
        },
        {
            "type": "divider"
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Log into GoSpotty here."
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Log in"
                },
                "value": "click_me_123",
                "url": "https://gospotty.herokuapp.com/",
                "action_id": "button-action"
            }
        }
    ])
    return Response(), 200


if __name__ == "__main__":
    app.run(debug=True, port=5002)
