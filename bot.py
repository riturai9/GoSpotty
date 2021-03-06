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

EXAMPLE_GENRE = 'dark trap, drill, hip hop, miami hip hop, rap, underground hip hop, uk alternative hip hop, uk hip hop'

slack_event_adapter = SlackEventAdapter(os.environ['SIGN_IN_SECRET'], '/slack/events', app)


@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    if BOT_ID != user_id:
        print(channel_id, text)


def get_message_blocks(items, empty_message, user, genre):
    blocks = []
    if len(items) == 0:
        blocks.extend([{
            "type": "divider"
        },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": empty_message
                }
            }, {
                "type": "divider"
            }])
    else:
        blocks.extend([{
            "type": "divider"
        },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f'Hey *{user}*, see the {genre} recommendations below :headphones:'
                }
            }])
        for item in items:
            print(item)
            blocks.extend([
                {
                    "type": "image",
                    "image_url": item.get('albumArt')[2].get('url'),
                    "alt_text": "album art"
                },
               {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f'{get_title(item)}'
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Preview Song"
                        },
                        "value": "click_me_123",
                        "url": item.get('previewUrl'),
                        "action_id": "button-action"
                    }
                }])
        blocks.append({
            "type": "divider"
        })
    return blocks


def get_title(item):
    return "*" + item.get('title') + "*" + " by " \
           + ", ".join(item.get('artists')) + " \n - " \
           + item.get('gcSpotifyUserFullName') + " is listening"


@app.route('/getRecommendation', methods=['POST'])
def get_recommendation():
    data = request.form
    genre = data.get('text')
    channel_id = data.get('channel_id')
    user_name = data.get('user_name')
    response = requests.get(f'https://gospotty.herokuapp.com/api/recommendations?genre={genre}')
    return_data = response.json().get('data').get('items')
    _message = f'Hey *{user_name}*, No songs found for genre: {genre} :worried:\n Please try something like: {EXAMPLE_GENRE} :crossed_fingers: '
    client.chat_postMessage(channel=channel_id, blocks=get_message_blocks(return_data, _message, user_name, genre))
    return Response(), 200


@app.route('/hotthisweek', methods=['POST'])
def hot_this_week():
    data = request.form
    channel_id = data.get('channel_id')
    user_name = data.get('user_name')
    response = requests.get("https://gospotty.herokuapp.com/api/recommendations/hotthisweek")
    return_data = response.json().get('data').get('items')
    _message = f'Hey {user_name}, No songs found for your query :worried:\n'
    client.chat_postMessage(channel=channel_id, blocks=get_message_blocks(return_data, _message, user_name, ""))
    return Response(), 200


@app.route('/login', methods=['POST'])
def login():
    data = request.form
    channel_id = data.get('channel_id')
    user_name = data.get('user_name')
    client.chat_postMessage(channel=channel_id, blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f'Hello *{user_name}*,\n welcome to the GoSpotty App. To continue please login'
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
                "text": "Log into GoSpotty here"
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
