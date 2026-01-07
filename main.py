from os import environ
from typing import Any

import discord
from discord import Intents, app_commands

from bot.bot import ChatBot
from chat_ai.chatai import AIParameters, ChatAI


def __parse_env_bool(val: str) -> bool:
    val = val.lower()
    if val in ["y", "yes", "t", "true", "on", "1"]:
        return True
    elif val in ["n", "no", "f", "false", "off", "0"]:
        return False
    else:
        raise ValueError(f"Invalid boolean value: {val}")


def __get_env_value(
    key: str, default: Any = None, parse_as: type | None = None, required: bool = False
) -> Any:
    val = environ.get(key, default)
    if val and parse_as:
        if parse_as is bool:
            val = __parse_env_bool(val)
        elif parse_as is float:
            val = float(val)
    if not val and required:
        raise ValueError(f"{key} must be set")
    return val


def main():
    # Configs
    # note: OPENAI_API_KEY is required but the OpenAI library grabs it on its own
    _ = __get_env_value("OPENAI_API_KEY", required=True)
    bot_name = __get_env_value("BOT_NAME", default="DiscordBot", required=False)
    debug = __get_env_value("DEBUG", default=False, parse_as=bool, required=False)
    discord_token = __get_env_value("DISCORD_BOT_TOKEN", required=True)
    model_name = __get_env_value("OPENAI_MODEL", required=True)
    guild_id = __get_env_value("DISCORD_SERVER_ID", required=True)

    # AI parameter overrides
    ai_temp = __get_env_value("AI_TEMPERATURE", "0.7", parse_as=float)
    ai_top_p = __get_env_value("AI_TOP_P", "0.9", parse_as=float)
    ai_frequency_penalty = __get_env_value(
        "AI_FREQUENCY_PENALTY", "0.7", parse_as=float
    )
    ai_presence_penalty = __get_env_value("AI_PRESENCE_PENALTY", "0.4", parse_as=float)

    ai_parameters = AIParameters(
        temperature=ai_temp,
        top_p=ai_top_p,
        frequency_penalty=ai_frequency_penalty,
        presence_penalty=ai_presence_penalty,
    )

    chat_ai = ChatAI(
        bot_name=bot_name,
        chat_history_length=50,
        model_name=model_name,
        ai_parameters=ai_parameters,
        debug=debug,
    )
    reaction_ai = ChatAI(
        bot_name="reactions",
        model_name="gpt-4o",
        chat_history_length=0,
        initial_prompt="Before every message, I will supply a list of strings that represent emojis. The list will begin with || and end with || and each emoji will be separated with a ,. After the emojis will be a message, I want you to take the message and choose a relevant emoji. For example, for this ||smile, cry, wave||Hello, you would respond with wave. ONLY respond with the emoji name",
        debug=debug,
    )
    discord_bot = ChatBot(
        chat_ai=chat_ai,
        reaction_ai=reaction_ai,
        guild_id=guild_id,
        intents=Intents.all(),
        debug=debug,
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

    @discord_bot.tree.context_menu(name="Textify")
    async def textify_message(
        interaction: discord.Interaction, message: discord.Message
    ):
        await discord_bot.textify_context(interaction, message)

    @discord_bot.tree.command(
        name="pushmem",
        description=f"Push a number of messages back in the channel's history into {bot_name}'s memory",
    )
    @app_commands.describe(
        number_messages=f"Number of messages in chat history to load into {bot_name}'s memory"
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

    discord_bot.run(discord_token)


if __name__ == "__main__":
    main()
