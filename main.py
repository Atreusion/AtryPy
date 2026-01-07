"""A very simple Discord bot.

Uses Ollama's local LLM API to generate responses based on the chat history of a specific channel.

Make sure to set the DISCORD_TOKEN, CHANNEL_ID, and MODEL_NAME environment
variables in a .env file or your system environment before running the bot.
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any

import discord
import ollama
from discord.ext import tasks
from dotenv import load_dotenv

# disable warnings for printing and commented-out code
# ruff: noqa: ERA001, T201

logging.basicConfig(level=logging.INFO)

# Load the variables from .env
load_dotenv()

# Access the variables from the environment
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2:latest")
STATE_FILE = Path(os.getenv("STATE_FILE", "last_run.txt"))
INTERVAL = int(os.getenv("INTERVAL", "0"))

def get_last_run() -> float:
    """Get the last run time from a file."""
    if STATE_FILE.exists():
        return float(STATE_FILE.read_text())
    return 0.0

def set_last_run() -> None:
    """Set the last run time to a file."""
    STATE_FILE.write_text(str(time.time()))

class MyClient(discord.Client):
    """Bot client that responds using a local LLM based on channel history."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize the bot client."""
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:
        """Create the background task and run it in the background."""
        # self.bg_task = self.loop.create_task(self.my_background_task())
        self.hourly_llm_task.start()

    @tasks.loop(hours=1)
    async def hourly_llm_task(self) -> None:
        """Fetch channel history and generate a response using the local LLM."""
        if time.time() - get_last_run() < INTERVAL:
            print("Skipping hourly run; interval not reached.")
            return  # Skip if run within the last hour
        set_last_run()
        channel = self.get_channel(CHANNEL_ID)
        if not isinstance(channel, discord.abc.Messageable):
            msg = "Channel is not messageable"
            raise TypeError(msg)
        # 1. Fetch history
        history = [
            f"[{msg.created_at.strftime('%H:%M')}] {msg.author.name}: {msg.clean_content}"
            async for msg in channel.history(limit=100)
            if msg.author != self.user
        ]

        # 2. Reverse history so it's chronological
        transcript = "\n".join(reversed(history))
        try:
            # We run the API call in a thread to keep the bot responsive
            """
            # Old generation method
            response = await asyncio.to_thread(
                ollama.generate,
                model=MODEL_NAME,
                prompt="Provide a brief, interesting science fact for the day.",
                keep_alive=0,
                options={"num_gpu": 0, "num_thread": 4},  # delete to use GPU
            )
            fact = response["response"]
            """
            response = ollama.chat(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": 'Predict the next message by atreusion in this Discord chat. Output ONLY the predicted message in the format "Username: Message".',
                    },
                    {
                        "role": "user",
                        "content": f"Here is the transcript:\n{transcript}\n\nNext message:",
                    },
                ],
                keep_alive=0,
                options={"num_gpu": 0, "num_thread": 4},  # delete/comment to use GPU
            )
            reply = response["message"]["content"][:500]  # limit to 500 chars just in case
            await channel.send(reply, silent=True)  # silent to avoid notifications

        except Exception as e:  # noqa: BLE001
            print(f"Local API Error: {e}")

    @hourly_llm_task.before_loop
    async def before_hourly_task(self) -> None:
        """Wait until the bot is ready before starting the task."""
        await self.wait_until_ready()

    async def on_ready(self) -> None:
        """Print a message when the bot is ready."""
        if self.user:
            print(f"Logged in as {self.user} (ID: {self.user.id})")
            print("------")

    async def my_background_task(self) -> None:
        """Unused background task that runs every 60 seconds."""
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)  # channel ID goes here

        # Tell the type checker that this is a messageable channel
        if not isinstance(channel, discord.abc.Messageable):
            msg = "Channel is not messageable"
            raise TypeError(msg)

        while not self.is_closed():
            # await channel.send(str(counter))
            messages = [message async for message in channel.history(limit=12)]
            for message in messages:
                print(message.author)
                print(message.content)
            await asyncio.sleep(60)  # task runs every 60 seconds


intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent to read message content

client = MyClient(intents=intents)

client.run(DISCORD_TOKEN)
