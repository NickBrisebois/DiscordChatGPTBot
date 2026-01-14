import argparse
import sys
from pathlib import Path

import discord
from discord import Intents, app_commands
from pymicroconf import ConfigHandler, InvalidConfigException

from bot.bot import ChatBot
from chat_ai.chatai_handler import ChatAIHandler
from config import Config


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--config", default="config.toml")
    args = args.parse_args()

    config_handler = ConfigHandler(
        config_file_path=Path(args.config), config_class=Config
    )

    try:
        config = config_handler.load_config()
    except InvalidConfigException as e:
        print("Invalid configuration:", e)
        sys.exit(1)

    chat_ai = ChatAIHandler(
        bot_name=config.bot_name,
        chat_history_length=config.openai.ai_parameters.max_tokens,
        model_name=config.openai.model_name,
        ai_parameters=config.openai.ai_parameters,
        debug=config.debug,
    )
    reaction_ai = ChatAIHandler(
        bot_name="reactions",
        model_name="gpt-4o",
        chat_history_length=0,
        initial_prompt="Before every message, I will supply a list of strings that represent emojis. The list will begin with || and end with || and each emoji will be separated with a ,. After the emojis will be a message, I want you to take the message and choose a relevant emoji. For example, for this ||smile, cry, wave||Hello, you would respond with wave. ONLY respond with the emoji name",
        ai_parameters=config.openai.ai_parameters,
        debug=config.debug,
    )
    discord_bot = ChatBot(
        chat_ai=chat_ai,
        reaction_ai=reaction_ai,
        guild_id=config.discord.guild_id,
        intents=Intents.all(),
        debug=config.debug,
    )

    @discord_bot.tree.command(
        name="clearhistory", description=f"Clear {config.bot_name}'s history"
    )
    async def clear_history(interaction: discord.Interaction):
        discord_bot.clear_history()
        await interaction.response.send_message("my memory is nice and empty :^)")

    @discord_bot.tree.command(
        name="synccommands", description=f"Update {config.bot_name}'s commands"
    )
    async def sync_commands(interaction: discord.Interaction):
        await discord_bot.tree.sync()
        await interaction.response.send_message(
            f"{config.bot_name}'s commands have been updated"
        )

    @discord_bot.tree.command(
        name="setprompt", description=f"Tell {config.bot_name} who he is"
    )
    @app_commands.describe(new_prompt="New system prompt")
    async def set_prompt(interaction: discord.Interaction, new_prompt: str):
        discord_bot.set_system_prompt(new_prompt)
        await interaction.response.send_message(
            f"{config.bot_name} is now prompted with {new_prompt}"
        )

    @discord_bot.tree.command(
        name="setemojis",
        description=f"Enable or disable {config.bot_name}'s emoji reactions",
    )
    @app_commands.describe(enabled="Enable or disable emoji reactions")
    async def set_emojis_enabled(
        interaction: discord.Interaction, enabled: bool = True
    ):
        discord_bot.set_emojis_enabled(enabled)
        await interaction.response.send_message(
            f"{config.bot_name} emoji reactions are now {'enabled' if enabled else 'disabled'}"
        )

    @discord_bot.tree.command(
        name=f"{config.bot_name}lonely", description=f"{config.bot_name} is lonely"
    )
    @app_commands.describe(number_messages="Number of messages to send")
    async def bot_is_lonely(
        interaction: discord.Interaction, number_messages: int = 10
    ):
        await interaction.response.send_message(
            f"{config.bot_name} is now so lonely he's going to talk to himself for a bit."
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

    @discord_bot.tree.context_menu(name="Textify")
    async def textify_message(
        interaction: discord.Interaction, message: discord.Message
    ):
        await discord_bot.textify_context(interaction, message)

    @discord_bot.tree.command(
        name="pushmem",
        description=f"Push a number of messages back in the channel's history into {config.bot_name}'s memory",
    )
    @app_commands.describe(
        number_messages=f"Number of messages in chat history to load into {config.bot_name}'s memory"
    )
    async def push_memory(
        interaction: discord.Interaction,
        number_messages: int = 10,
    ) -> None:
        try:
            await interaction.response.defer()

            if interaction.channel:
                await discord_bot.load_channel_history(
                    channel=interaction.channel, num_messages=number_messages
                )

                await interaction.followup.send("Injected memory juice")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

    discord_bot.run(config.discord.token)


if __name__ == "__main__":
    main()
