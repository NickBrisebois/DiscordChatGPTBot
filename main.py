from os import environ

import discord
from chat_ai.chatai import ChatAI
from bot.bot import ChatBot
from discord import app_commands
from discord import Intents


def main():
    # Configs
    # note: OPENAI_API_KEY is used implicitly by the openai library
    bot_name = environ.get("BOT_NAME")
    discord_token = environ.get("DISCORD_BOT_TOKEN")
    model_name = environ.get("OPENAI_MODEL")
    discord_server_id = environ.get("DISCORD_SERVER_ID")
    read_all_messages = environ.get("READ_ALL_MESSAGES", "false").lower() == "true"

    chat_ai = ChatAI(bot_name=bot_name, model_name=model_name)
    discord_bot = ChatBot(
        chat_ai=chat_ai,
        discord_server_id=discord_server_id,
        read_all_messages=read_all_messages,
        intents=Intents.all()
    )

    @discord_bot.tree.command(name="clearhistory", description=f"Clear {bot_name}'s history")
    async def clear_history(interaction: discord.Interaction):
        discord_bot.clear_history()
        await interaction.response.send_message("my memory is nice and empty :^)")

    @discord_bot.tree.command(name="setprompt", description=f"Tell {bot_name} who he is")
    @app_commands.describe(new_prompt="New system prompt")
    async def set_prompt(interaction: discord.Interaction, new_prompt: str):
        discord_bot.set_system_prompt(new_prompt)
        await interaction.response.send_message(
            f"{bot_name} is now prompted with {new_prompt}"
        )

    discord_bot.run(discord_token)

if __name__ == "__main__":
    main()
