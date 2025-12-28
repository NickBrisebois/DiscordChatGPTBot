from os import environ

import discord
from discord import Intents, app_commands

from bot.bot import ChatBot
from chat_ai.chatai import ChatAI


def main():
    # Configs
    # note: OPENAI_API_KEY is used implicitly by the openai library
    bot_name = environ.get("BOT_NAME", "DiscordBot")
    discord_token = environ["DISCORD_BOT_TOKEN"]
    model_name = environ["OPENAI_MODEL"]
    guild_id = environ["DISCORD_SERVER_ID"]
    read_all_messages = environ.get("READ_ALL_MESSAGES", "false").lower() == "true"

    chat_ai = ChatAI(bot_name=bot_name, chat_history_length=50, model_name=model_name)
    reaction_ai = ChatAI(
        bot_name="reactions",
        model_name="gpt-4o",
        chat_history_length=0,
        initial_prompt="Before every message, I will supply a list of strings that represent emojis. The list will begin with || and end with || and each emoji will be separated with a ,. After the emojis will be a message, I want you to take the message and choose a relevant emoji. For example, for this ||smile, cry, wave||Hello, you would respond with wave. ONLY respond with the emoji name",
    )
    discord_bot = ChatBot(
        chat_ai=chat_ai,
        reaction_ai=reaction_ai,
        read_all_messages=read_all_messages,
        guild_id=guild_id,
        intents=Intents.all(),
    )

    @discord_bot.tree.command(
        name="clearhistory", description=f"Clear {bot_name}'s history"
    )
    async def clear_history(interaction: discord.Interaction):
        discord_bot.clear_history()
        await interaction.response.send_message("my memory is nice and empty :^)")

    @discord_bot.tree.command(
        name="synccommands", description=f"Update {bot_name}'s commands"
    )
    async def sync_commands(interaction: discord.Interaction):
        await discord_bot.tree.sync()
        await interaction.response.send_message(
            f"{bot_name}'s commands have been updated"
        )

    @discord_bot.tree.command(
        name="setprompt", description=f"Tell {bot_name} who he is"
    )
    @app_commands.describe(new_prompt="New system prompt")
    async def set_prompt(interaction: discord.Interaction, new_prompt: str):
        discord_bot.set_system_prompt(new_prompt)
        await interaction.response.send_message(
            f"{bot_name} is now prompted with {new_prompt}"
        )

    @discord_bot.tree.command(
        name="setemojis",
        description=f"Enable or disable {bot_name}'s emoji reactions",
    )
    @app_commands.describe(enabled="Enable or disable emoji reactions")
    async def set_emojis_enabled(
        interaction: discord.Interaction, enabled: bool = True
    ):
        discord_bot.set_emojis_enabled(enabled)
        await interaction.response.send_message(
            f"{bot_name} emoji reactions are now {'enabled' if enabled else 'disabled'}"
        )

    @discord_bot.tree.command(
        name=f"{bot_name}lonely", description=f"{bot_name} is lonely"
    )
    @app_commands.describe(number_messages="Number of messages to send")
    async def bot_is_lonely(
        interaction: discord.Interaction, number_messages: int = 10
    ):
        await interaction.response.send_message(
            f"{bot_name} is now so lonely he's going to talk to himself for a bit."
        )
        await discord_bot.bot_is_lonely(
            num_messages=number_messages, channel=interaction.channel
        )

    @discord_bot.tree.context_menu(name="Gigafy")
    async def gigafy_message(
        interaction: discord.Interaction, message: discord.Message
    ):
        await discord_bot.gigafy_context(interaction=interaction, message=message)

    @discord_bot.tree.context_menu(name="Mikuify")
    async def mikuify_message(
        interaction: discord.Interaction, message: discord.Message
    ):
        await discord_bot.mikuify_context(interaction=interaction, message=message)

    @discord_bot.tree.context_menu(name="Emojify")
    async def emojify_message(
        interaction: discord.Interaction, message: discord.Message
    ):
        await discord_bot.emojify_message(interaction=interaction, message=message)

    discord_bot.run(discord_token)


if __name__ == "__main__":
    main()
