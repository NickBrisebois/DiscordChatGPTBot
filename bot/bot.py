import random
import discord
from discord import Intents
from discord import app_commands
from discord.ext import commands

from chat_ai.chatai import ChatAI


class ChatBot(commands.Bot):
    def __init__(self, chat_ai: ChatAI, intents: Intents) -> None:
        self._chat_ai = chat_ai     
        super().__init__(intents=intents, command_prefix="!")

    async def setup_hook(self):
        self.tree.copy_global_to(guild=discord.Object(id=858851324043722752))
        await self.tree.sync(guild=discord.Object(id=858851324043722752))

    async def on_ready(self) -> None:
        print("Logged on as", self.user)

    def clear_history(self) -> None:
        self._chat_ai.clear_history()

    def set_system_prompt(self, text: str) -> None:
        self._chat_ai.set_system_prompt(text=text)

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user:
            return

        username = self.user.name+"#"+self.user.discriminator

        has_mentioned = False
        for mention in message.mentions:
            if str(mention) == username:
                has_mentioned = True

        if has_mentioned or random.random() > float(0.96):
            async with message.channel.typing():
                if "<@676962651103821826> " in message.content:
                    msg_text = message.content.split("<@676962651103821826> ")[1]
                else:
                    msg_text = message.content
                ai_response = await self._chat_ai.get_response(message.author.id, msg_text) 
            await message.channel.send(ai_response)
