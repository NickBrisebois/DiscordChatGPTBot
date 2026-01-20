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
OPENAI_API_KEY=sk-R-XXXXXXXXXXXXXXXXXXXXXX.... # get this from here https://platform.openai.com/api-keys
DISCORD_TOKEN=XXXXXXXXXXXXXXXX.... # get this from here https://discord.com/developers/applications
DISCORD_GUILD_ID=8588513XXXXXXXXXXX # right click on the server and hit copy server ID. This is the server the chat commands get installed to
OPENAI_MODEL_NAME=ft-gpt-4o-mini-2024-07-18:personal:xxxxxxxxxxxxx # fine tune here https://platform.openai.com/finetune

BOT_NAME=lez # what's the name of this bot?
```

You can also tweak the AI a bit further with these env vars but they're all optional:
``` bash
TEMPERATURE=0.9
TOP_P=0.95
FREQUENCY_PENALTY=0.0
PRESENCE_PENALTY=0.0
MAX_TOKENS=500
MAX_HISTORY_SIZE=50
```

All of the above env vars can also be configured with `config.toml`

Features:
  - Channel specific memory (hardcoded to 50 messages but easily changeable)
  - Can be DM'd for private conversation where you don't need to @ the bot
  - Randomly replies to a message every once and a while (2% chance, modify in bot.py)
