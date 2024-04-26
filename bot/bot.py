import random
import discord
from discord import Intents

from chat_ai.chatai import ChatAI


class ChatBot(discord.Client):
    def __init__(self, chat_ai: ChatAI, intents=Intents) -> None:
        self._chat_ai = chat_ai     
        super().__init__(intents=intents)

    async def on_ready(self) -> None:
        print("Logged on as", self.user)
    
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
