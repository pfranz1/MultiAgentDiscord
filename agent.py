import discord
from discord_connection import DiscordConnection
from messagehistory import MessageHistory


# I want to tightly control what messages this agent considers when responding, so despite being able to read from discord,
# this agent will delegate reading and writing to the connection
class Agent(discord.Client):
    def __init__(self, name, connection : DiscordConnection, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.connection = connection
        self.consideredMessageHistories = []

    async def on_ready(self):
        print(f'Agent:{self.name} is connected as {self.user}')

    async def respond(self):
        agent_view_of_channel = self.get_channel( self.connection.current_channel.id)
        async with agent_view_of_channel.typing():
            # todo: agent logic

            flat_messages = [msg for h in self.consideredMessageHistories for msg in h.messages]

            response = f'Hello! I am {self.name}! {len(flat_messages)} messages!'

            # respond
            await agent_view_of_channel.send(response)

    def register_state(self, state: MessageHistory):
        self.consideredMessageHistories.append(state)