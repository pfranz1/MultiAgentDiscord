import discord
import asyncio

# Made the choice for just one reading bot, which is the only bot that will not speak.
class DiscordConnection(discord.Client):
    # Exposes user_message_queue allowing for a pub sub from discord

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.user_message_queue = asyncio.Queue() # Start the queue that will be awaited on for user messages
        self.current_channel = None # we will speak only in one channel, which is the last one the user spoke in, mvp changing channel changes nothing

    async def on_ready(self):
        print(f'The connection has been created with {self.user}')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')

        #todo: have some way to check if it is a user message or an agent message (maybe with roles)
        if message.author == self.user:
            return

        if message.content.startswith('$'):
            # Remember this is the channel that is being spoken in
            self.current_channel = message.channel

            # Throw the message into the queue
            # Maybe I should process the message into the langchain user version
            self.user_message_queue.put_nowait(message)
