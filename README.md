# A discord bot that works with fine-tuned OpenAI models

A Discord bot that wraps around OpenAI models via their API. Can either be set to use a
fine-tuned model or one of the base models.

To install the libraries for it you'll need to install the Python package manager: [uv](https://docs.astral.sh/uv/)

Once you have `uv`, enter the cloned directory in your terminal and type
```bash
uv sync
```

To run you'll need these env vars:
``` bash
OPENAI_API_KEY: sk-R-XXXXXXXXXXXXXXXXXXXXXX.... # get this from here https://platform.openai.com/api-keys
DISCORD_BOT_TOKEN: XXXXXXXXXXXXXXXX.... # get this from here https://discord.com/developers/applications
DISCORD_SERVER_ID: 8588513XXXXXXXXXXX # right click on the server and hit copy server ID. This is the server the chat commands get installed to
OPENAI_MODEL: ft-gpt-4o-mini-2024-07-18:personal:xxxxxxxxxxxxx # fine tune here https://platform.openai.com/finetune

BOT_NAME: lez # what's the name of this bot?
READ_ALL_MESSAGES: true/false # should the bot insert every message into the chat history, even if it doesn't reference the bot?
```

Features:
  - Channel specific memory (hardcoded to 50 messages but easily changeable)
  - Can be DM'd for private conversation where you don't need to @ the bot
  - Randomly replies to a message every once and a while (2% chance, modify in bot.py)
