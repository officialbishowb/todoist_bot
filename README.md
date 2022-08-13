# Todoist API Bot

## Description

This bot is based on Todoist Python SDK.
It can be used to create tasks in Todoist, list them and delete them.
Beside that it can also be used to enable reminders for those task that have date and time set in Todist (as todoist offers reminder only for Premium users).

### Requirements
- Todoist [API](https://developer.todoist.com/rest/v1/) Key
- Telegram Bot Token

Set them as environment variables:

```env
TODOIST_TOKEN = <your-todoist-token>
BOT_TOKEN = <your-telegram-bot-token>
ACCESS_ID = <telegram-user-ids> (who can use the bot)
```


### Steps to run the bot

1.) Clone the repository

2.) Run `pip install -r requirements.txt`

3.) Setup the environment variables

4.) Run `python bot.py`

---
Author - me



