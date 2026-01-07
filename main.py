import asyncio
import logging
import os

import discord
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

# Load the variables from .env
load_dotenv()

# Access the variable
TOKEN = os.getenv("DISCORD_TOKEN", "")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", ""))


class MyClient(discord.Client):
    # Suppress error on the User attribute being None since it fills up later
    user: discord.ClientUser  # pyright: ignore[reportIncompatibleMethodOverride]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:
        # create the background task and run it in the background
        self.bg_task = self.loop.create_task(self.my_background_task())

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

    async def my_background_task(self):
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)  # channel ID goes here

        # Tell the type checker that this is a messageable channel
        if not isinstance(channel, discord.abc.Messageable):
            msg = "Channel is not messageable"
            raise TypeError(msg)

        while not self.is_closed():
            # await channel.send(str(counter))
            print(1)
            messages = [message async for message in channel.history(limit=12)]
            m_content = [message.content for message in messages]
            print(m_content)
            print(2)
            await asyncio.sleep(6)  # task runs every 60 seconds


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)

client.run(TOKEN)
