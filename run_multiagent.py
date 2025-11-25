import asyncio

import discord
import os
from dotenv import load_dotenv

from agent import Agent
from discord_connection import DiscordConnection

load_dotenv()

DISCORD_TOKEN_1 = os.getenv('DISCORD_TOKEN_1')
DISCORD_TOKEN_2 = os.getenv('DISCORD_TOKEN_2')
DISCORD_TOKEN_3 = os.getenv('DISCORD_TOKEN_3')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')


async def main_scenario():
    intents = discord.Intents.default()
    intents.message_content = True

    discord_connection = DiscordConnection(intents=intents)

    # Init Agents
    agent = Agent("first", discord_connection,intents=intents)

    async def echo():
        while True:
            await discord_connection.user_message_queue.get()
            await agent.respond()

    await asyncio.gather(discord_connection.start(DISCORD_TOKEN_1),
                         agent.start(DISCORD_TOKEN_2), echo(), )


if __name__ == '__main__':
    asyncio.run(main_scenario())
