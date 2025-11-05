import os
from dotenv import load_dotenv
import discord

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged in as self {self.user}')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')

        if message.author == client.user:
            return

        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')

intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run(DISCORD_TOKEN)