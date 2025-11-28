import discord
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

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

        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
        self.agent = create_agent(
            model=self.llm,
        )

    async def on_ready(self):
        print(f'Agent:{self.name} is connected as {self.user}')

    async def respond(self):
        agent_view_of_channel = self.get_channel( self.connection.current_channel.id)
        async with agent_view_of_channel.typing():
            flat_messages = [msg for h in self.consideredMessageHistories for msg in h.messages]
            response = self.agent.invoke({"messages": flat_messages})
            response_content = response['messages'][-1].content
            if len(response_content) > 2000:
                response_content = response_content[:2000]

            for i, msg in enumerate(response["messages"]):
                msg.pretty_print()
            # respond
            await agent_view_of_channel.send(response_content)

    def register_state(self, state: MessageHistory):
        self.consideredMessageHistories.append(state)