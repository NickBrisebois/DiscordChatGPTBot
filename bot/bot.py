import asyncio
import random

import discord
from discord import DMChannel, Intents
from discord.ext import commands

from chat_ai.chatai import ChannelMemoryItem, ChatAI, ChatAIException, Role

REPLY_CHANCE = 0.01
EMOJI_REPLY_CHANCE = 0.005


class ChatBot(commands.Bot):
    def __init__(
        self,
        chat_ai: ChatAI,
        reaction_ai: ChatAI,
        read_all_messages: bool,
        intents: Intents,
        guild_id: str | None = None,
    ) -> None:
        self._chat_ai = chat_ai
        self._reaction_ai = reaction_ai
        self._read_all_messages = read_all_messages
        self._guild_id = discord.Object(id=str(guild_id)) if guild_id else None

        self._emojis_enabled = True

        super().__init__(intents=intents, command_prefix="!")

    async def setup_hook(self):
        try:
            synced = await self.tree.sync(guild=self._guild_id)
            print(f"Synced {len(synced)} commands.")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

    async def on_ready(self) -> None:
        print("Logged on as", self.user)

    def clear_history(self) -> None:
        self._chat_ai.clear_history(clear_all_channels=True)

    def set_system_prompt(self, text: str) -> None:
        self._chat_ai.set_system_prompt(text=text)

    def set_emojis_enabled(self, enabled: bool) -> None:
        self._emojis_enabled = enabled

    @property
    def _at_code(self) -> str:
        if not self.user:
            raise ValueError("User not initialized")

        return f"<@{self.user.id}>"

    async def _react_to_message(self, message: discord.Message) -> None:
        emojis = self._get_emojis(message=message)
        channel_id = message.channel.id
        input_text = f"||{','.join(emojis.keys())}||{message.content}"
        reaction = await self._reaction_ai.get_response(
            channel_id=str(channel_id), message_text=input_text
        )

        if reaction in emojis:
            await message.add_reaction(emojis[reaction])

    async def load_channel_history(
        self, channel: discord.TextChannel, num_messages: int
    ) -> None:
        messages = []
        async for message in channel.history(limit=num_messages):
            if message.author == self.user:
                messages.append((message, Role.assistant))
            else:
                messages.append((message, Role.user))

        messages.reverse()

        memory_items = [
            ChannelMemoryItem(
                text=message.content,
                username=message.author.display_name
                if role == Role.user
                else self._chat_ai._bot_name,
                role=role,
            )
            for message, role in messages
        ]

        if memory_items:
            self._chat_ai.initialise_channel_history(
                channel_id=str(channel.id), messages=memory_items
            )

    async def _light_but_rich_snack(self, message: discord.Message) -> None:
        sticker = await self.fetch_sticker(1314648578039218176)
        await message.channel.send(stickers=[sticker])

    def _get_emojis(
        self, message: discord.Message, search_prefix: str | None = None
    ) -> dict[str, discord.Emoji]:
        emojis = {}
        for emoji in message.guild.emojis:
            if search_prefix and not emoji.name.lower().startswith(
                search_prefix.lower()
            ):
                continue
            emojis[emoji.name] = emoji

        return emojis

    async def emojify_message(
        self,
        interaction: discord.Interaction,
        message: discord.Message,
        emoji_prefix: str = "",
    ):
        """Right-click context menu command to emojify any message"""
        emojis = self._get_emojis(message=message, search_prefix=emoji_prefix)

        if not emojis:
            await interaction.response.send_message(
                "No emojis found in this server.", ephemeral=True
            )
            return

        await interaction.response.send_message("Emojifying message...", ephemeral=True)
        reaction_tasks = [message.add_reaction(emoji) for emoji in emojis.values()]

        try:
            results = await asyncio.gather(*reaction_tasks, return_exceptions=True)
            successful = sum(
                1 for result in results if not isinstance(result, Exception)
            )
            failed = len(results) - successful

            if failed > 0:
                await interaction.edit_original_response(
                    content=f"❌ Failed to add {failed} reactions."
                )
        except Exception as e:
            await interaction.edit_original_response(
                content=f"Failed to emojify message :(((( (err: {e})"
            )
            return

        if successful > 0:
            await interaction.edit_original_response(
                content=f"✅ Successfully added {successful} <{emoji_prefix}> emojis."
            )

    async def mikuify_context(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        """Right-click context menu command to mikuify any message"""
        await self.emojify_message(interaction, message, emoji_prefix="miku")

    async def gigafy_context(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        """Right-click context menu command to gigafy any message"""
        await self.emojify_message(interaction, message, emoji_prefix="giga")

    async def bot_is_lonely(
        self, num_messages: int, channel: discord.TextChannel
    ) -> None:
        for i in range(num_messages):
            pass
            # await self._send_message(
            #     channel_id=str(channel.id),
            #     message = await self._chat_ai.get_response(channel_id=str(channel.id)),
            # )

    async def on_message(self, message: discord.Message) -> None:
        if self._chat_ai._bot_name.lower() in message.content.lower() or (
            random.random() <= float(EMOJI_REPLY_CHANCE) and self._emojis_enabled
        ):
            await self._react_to_message(message)

        if not self.user or message.author == self.user:
            return

        if message.stickers:
            if message.stickers[0].id == 1314648578039218176:
                await self._light_but_rich_snack(message=message)

        msg_text = message.content
        if self._at_code in message.content:
            msg_text = message.content.split(self._at_code)[1]

        username = self.user.name + "#" + self.user.discriminator

        has_mentioned = False
        for mention in message.mentions:
            if str(mention) == username:
                has_mentioned = True

        if (
            isinstance(message.channel, DMChannel)
            or has_mentioned
            or random.random() <= float(REPLY_CHANCE)
        ):
            async with message.channel.typing():
                try:
                    ai_response = await self._chat_ai.get_response(
                        channel_id=str(message.channel.id),
                        message_text=msg_text,
                        reply_to_username=message.author.name,
                    )

                    if has_mentioned:
                        reply_to = await message.channel.fetch_message(message.id)
                        await message.channel.send(ai_response, reference=reply_to)
                        return

                    await message.channel.send(ai_response)
                except ChatAIException as e:
                    await message.channel.send(
                        f"😰 {username} broke and couldn't respond (error: {e})"
                    )
                except Exception as e:
                    await message.channel.send(
                        f"😵 {username} *really* broke and couldn't respond (what did you do?) (error: {e})"
                    )
