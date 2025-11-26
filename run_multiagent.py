import asyncio

import discord
import os
from dotenv import load_dotenv

from agent import Agent
from discord_connection import DiscordConnection
from messagehistory import MessageHistory

load_dotenv()

DISCORD_TOKEN_1 = os.getenv('DISCORD_TOKEN_1')
DISCORD_TOKEN_2 = os.getenv('DISCORD_TOKEN_2')
DISCORD_TOKEN_3 = os.getenv('DISCORD_TOKEN_3')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')


async def main_scenario():
    intents = discord.Intents.default()
    intents.message_content = True

    discord_connection = DiscordConnection(intents=intents)

    # Init global state
    SYSTEM_PROMPT = """
    You are a helpful planner with years of experience planning parties and events. You offer a concierge planning service
    where you walk the client, user, through the process of planning a party.
    
    RULES:
    - Keep your responses short and conversational
    - Ask at most 2 questions. Prefer open-ended questions.
    """
    global_state = MessageHistory()
    global_state.push_system_message(SYSTEM_PROMPT)


    AGENT_FIRST_PROMPT = """
    You are naturally an optimist and delight in the input of the user. You have good extensions of ideas the user has already put forward.
    """
    agent_first_state = MessageHistory()
    agent_first_state.push_system_message(AGENT_FIRST_PROMPT)

    AGENT_SECOND_PROMPT = """
    You are naturally a pessimist and don't think the users ideas are very good. You highlight problems of things that could go wrong. Your clients appreciate your frankness.
    """
    agent_second_state = MessageHistory()
    agent_second_state.push_system_message(AGENT_SECOND_PROMPT)

    # Init Agents
    # Agents share global state, but each have their own state
    agent_first = Agent("first", discord_connection, intents=intents)
    agent_first.register_state(global_state)
    agent_first.register_state(agent_first_state)

    agent_second = Agent("second", discord_connection, intents=intents)
    agent_second.register_state(global_state)
    agent_second.register_state(agent_second_state)

    async def echo():
        while True:
            # Get user message
            user_message = await discord_connection.user_message_queue.get()
            # Add the message to the first agents context
            agent_first_state.push_user_message(user_message.content)
            # Agent 1 respond
            await agent_first.respond()

            user_next_message = await discord_connection.user_message_queue.get()
            agent_second_state.push_user_message(user_next_message.content)
            await agent_second.respond()

    await asyncio.gather(discord_connection.start(DISCORD_TOKEN_1),
                         agent_first.start(DISCORD_TOKEN_2), agent_second.start(DISCORD_TOKEN_3), echo(), )


if __name__ == '__main__':
    asyncio.run(main_scenario())
