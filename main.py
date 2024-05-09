import discord
from chat_ai.chatai import ChatAI
from bot.bot import ChatBot
from discord import app_commands
from discord import Intents
import asyncio


def main():
    chat_ai = ChatAI()
    discord_bot = ChatBot(chat_ai=chat_ai, intents=Intents.all())

    @discord_bot.tree.command(name="clearhistory", description="Clear lez's history")
    async def clear_history(interaction: discord.Interaction):
        discord_bot.clear_history()
        await interaction.response.send_message("my memory is nice and empty :^)")

    @discord_bot.tree.command(name="setprompt", description="Tell lez who he is")
    @app_commands.describe(new_prompt="New system prompt")
    async def set_prompt(interaction: discord.Interaction, new_prompt: str):
        discord_bot.set_system_prompt(new_prompt)
        await interaction.response.send_message(
            f"lez is now prompted with {new_prompt}"
        )

    # discord_bot.run("NzY0NTY5MTM0NzkyMDQ4NjYw.G_9q9K.WR4FWE26-Yron2-TB0G7bzsksoboDKVoNREwcA")
    discord_bot.run("Njc2OTYyNjUxMTAzODIxODI2.GI6boT.gmNkZ94PatwxL5HplUchyic5Xl_vnlaml5ZdCg")

if __name__ == "__main__":
    main()
