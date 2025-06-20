import asyncio
import random
from typing import List
import discord
from discord import DMChannel, Intents
from discord.ext import commands

from chat_ai.chatai import ChatAI, Role


class ChatBot(commands.Bot):
    def __init__(
        self,
        chat_ai: ChatAI,
        reaction_ai: ChatAI,
        read_all_messages: bool,
        intents: Intents,
    ) -> None:
        self._chat_ai = chat_ai
        self._reaction_ai = reaction_ai
        self._read_all_messages = read_all_messages

        self._emojis_enabled = True

        super().__init__(intents=intents, command_prefix="!")

    async def setup_hook(self):
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands.")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

    async def on_ready(self) -> None:
        print("Logged on as", self.user)

    def clear_history(self) -> None:
        self._chat_ai.clear_history(clear_all=True)

    def set_system_prompt(self, text: str) -> None:
        self._chat_ai.set_system_prompt(text=text)

    def set_emojis_enabled(self, enabled: bool) -> None:
        self._emojis_enabled = enabled

    @property
    def _at_code(self) -> str:
        return f"<@{self.user.id}>"

    async def _react_to_message(self, message: discord.Message) -> None:
        emojis = self._get_emojis(message=message)
        channel_id = message.channel.id
        input_text = f"||{','.join(emojis.keys())}||{message.content}"
        self._reaction_ai.append_history(
            channel_id=str(channel_id),
            role=Role.user,
            message=input_text,
        )
        reaction = await self._reaction_ai.get_response(channel_id=str(channel_id))
        await message.add_reaction(emojis[reaction])

    async def _light_but_rich_snack(self, message: discord.Message) -> None:
        sticker = await self.fetch_sticker(1314648578039218176)
        await message.channel.send(stickers=[sticker])

    def _get_emojis(self, message: discord.Message, search_prefix: str | None = None) -> dict[str, discord.Emoji]:
        emojis = {}
        for emoji in message.guild.emojis:
            if search_prefix and not emoji.name.lower().startswith(search_prefix.lower()):
                continue
            emojis[emoji.name] = emoji

        return emojis

    async def gigafy_context(self, interaction: discord.Interaction, message: discord.Message):
        """Right-click context menu command to gigafy any message"""
        giga_emojis = self._get_emojis(message=message, search_prefix="giga")
        
        if not giga_emojis:
            await interaction.response.send_message("No 'giga' emojis found in this server.", ephemeral=True)
            return

        await interaction.response.send_message("Gigafying message...", ephemeral=True)
        reaction_tasks = [
            message.add_reaction(emoji) for emoji in giga_emojis.values()
        ]

        try:
            results = await asyncio.gather(*reaction_tasks, return_exceptions=True)
            successful = sum(1 for result in results if not isinstance(result, Exception))
            failed = len(results) - successful
            
            if successful > 0:
                await interaction.channel.send(f"✅ Added {successful} giga reactions to! (triggered by {interaction.user.mention})")
            else:
                await interaction.edit_original_response(content="❌ Failed to add any reactions.")
        except Exception as e:
            await interaction.edit_original_response(content=f"Failed to gigafy message :(((( (err: {e})")
            return


    async def on_message(self, message: discord.Message) -> None:
        if self._chat_ai._bot_name.lower() in message.content.lower() or (
            random.random() > float(0.99) and self._emojis_enabled
        ):
            await self._react_to_message(message)

        if message.author == self.user:
            return

        if message.stickers:
            if message.stickers[0].id == 1314648578039218176:
                await self._light_but_rich_snack(message=message)

        if self._read_all_messages:
            # if read all messages is enabled, we add all messages to the bot history, even if they don't mention the bot
            if self._at_code in message.content:
                msg_text = message.content.split(self._at_code)[1]
            else:
                msg_text = message.content

            self._chat_ai.append_history(
                channel_id=str(message.channel.id),
                role=Role.user,
                message=msg_text,
            )

        username = self.user.name + "#" + self.user.discriminator

        has_mentioned = False
        for mention in message.mentions:
            if str(mention) == username:
                has_mentioned = True

        if (
            isinstance(message.channel, DMChannel)
            or has_mentioned
            or random.random() > float(0.98)
        ):
            # if read all messages is disabled, we'll *only* read messages that mention the bot
            if not self._read_all_messages:
                if self._at_code in message.content:
                    msg_text = message.content.split(self._at_code)[1]
                else:
                    msg_text = message.content

                self._chat_ai.append_history(
                    channel_id=str(message.channel.id),
                    role=Role.user,
                    message=msg_text,
                )

            async with message.channel.typing():

                channel_id = str(message.channel.id)
                ai_response = await self._chat_ai.get_response(channel_id=channel_id)

                self._chat_ai.append_history(
                    channel_id=channel_id, role=Role.assistant, message=ai_response
                )
            await message.channel.send(ai_response)
