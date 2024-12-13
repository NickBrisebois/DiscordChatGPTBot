import random
import discord
from discord import DMChannel, Intents
from discord.ext import commands

from chat_ai.chatai import ChatAI, Role


class ChatBot(commands.Bot):
    def __init__(
        self,
        chat_ai: ChatAI,
        discord_server_id: str,
        read_all_messages: bool,
        intents: Intents,
    ) -> None:
        self._chat_ai = chat_ai
        self._discord_server_id = discord_server_id
        self._read_all_messages = read_all_messages
        super().__init__(intents=intents, command_prefix="!")

    async def setup_hook(self):
        self.tree.copy_global_to(guild=discord.Object(id=self._discord_server_id))
        await self.tree.sync(guild=discord.Object(id=self._discord_server_id))

    async def on_ready(self) -> None:
        print("Logged on as", self.user)

    def clear_history(self) -> None:
        self._chat_ai.clear_history()

    def set_system_prompt(self, text: str) -> None:
        self._chat_ai.set_system_prompt(text=text)

    @property
    def _at_code(self) -> str:
        return f"<@{self.user.id}>"

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user:
            return

        if self._read_all_messages:
            # if read all messages is enabled, we add all messages to the bot history, even if they don't mention the bot
            self._chat_ai.append_history(
                channel_id=str(message.channel.id),
                role=Role.user,
                message=message.content,
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
                self._chat_ai.append_history(
                    channel_id=str(message.channel.id),
                    role=Role.user,
                    message=message.content,
                )

            async with message.channel.typing():
                if self._at_code in message.content:
                    msg_text = message.content.split(self._at_code)[1]
                else:
                    msg_text = message.content

                channel_id = str(message.channel.id)
                ai_response = await self._chat_ai.get_response(
                    channel_id=channel_id, input_text=msg_text
                )

                self._chat_ai.append_history(
                    channel_id=channel_id, role=Role.assistant, message=ai_response
                )
            await message.channel.send(ai_response)
