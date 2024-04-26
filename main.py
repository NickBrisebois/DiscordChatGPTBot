from chat_ai.chatai import ChatAI
from bot.bot import ChatBot
from discord import Intents


def main():
    chat_ai = ChatAI()
    discord_bot = ChatBot(chat_ai=chat_ai, intents=Intents.all())
    # discord_bot.run("NzY0NTY5MTM0NzkyMDQ4NjYw.G_9q9K.WR4FWE26-Yron2-TB0G7bzsksoboDKVoNREwcA")
    discord_bot.run("Njc2OTYyNjUxMTAzODIxODI2.GI6boT.gmNkZ94PatwxL5HplUchyic5Xl_vnlaml5ZdCg")


if __name__ == "__main__":
    main()
