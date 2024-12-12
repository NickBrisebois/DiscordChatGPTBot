# A discord bot that works with fine-tuned OpenAI fine tuned models

Rather lazily programmed discord bot that works with any OpenAI models. 

To install the libraries for it you'll need to install the Python package manager `poetry`

To run you'll need these env vars:
```
OPENAI_API_KEY: <api key> # get this from here https://platform.openai.com/api-keys
DISCORD_BOT_TOKEN: <token> # get this from here https://discord.com/developers/applications
OPENAI_MODEL: ft-gpt-4o-mini-2024-07-18:personal:xxxxxxxxxxxxx # fine tune here https://platform.openai.com/finetune
BOT_NAME: lez # what's the name of this bot?
```

Features:
  - Channel specific memory (hardcoded to 50 messages but easily changeable)
  - Can be DM'd for private conversation where you don't need to @ the bot
