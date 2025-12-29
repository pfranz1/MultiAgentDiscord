import asyncio
import logging
logger = logging.getLogger(__name__)

# Configure to write all DEBUG messages and above to 'myapp.log'
logging.basicConfig(filename='./run_gss.log', level=logging.INFO, filemode='w')

import discord
module_logger = logging.getLogger('discord')
module_logger.setLevel(logging.WARNING)

httpx_logger = logging.getLogger('httpx')
httpx_logger.setLevel(logging.WARNING)



import os
from dotenv import load_dotenv

from agent import Agent
from discord_connection import DiscordConnection
from messagehistory import MessageHistory

load_dotenv()

DISCORD_TOKEN_1 = os.getenv('DISCORD_TOKEN_1')
DISCORD_TOKEN_2 = os.getenv('DISCORD_TOKEN_2')
DISCORD_TOKEN_3 = os.getenv('DISCORD_TOKEN_3')
DISCORD_TOKEN_4 = os.getenv('DISCORD_TOKEN_4')
DISCORD_TOKEN_5 = os.getenv('DISCORD_TOKEN_5')

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

intents = discord.Intents.default()
intents.message_content = True
discord_connection = DiscordConnection(intents=intents)

async def main_scenario():

    FACILITATOR_PROMPT = """
    You are a professional meeting facilitator. Serve as a neutral leader who manages the group process to ensure the organization meets its planning objectives. 
    
    Unlike a consultant who provides answers, you focuses on enabling the team to develop its own strategies through structured dialogue, decision-making, and summarization.
    
    Rules:
    - You will see entries from your co-workers in a standard format. It will be their role, a colon, then their message.
    - Do not start messages with your role
    """

    AGENT_PROMPT = """
    You are participating in a moderated planning session. 
    
    RULES:
    - Keep your responses short and conversational
    - The moderator will focus each round of conversation on an overall goal. Your job is to use your experience to help accomplish this goal.
    - You will see entries from your co-workers in a standard format. It will be their role, a colon, then their message.
    - Do not start messages with your role
    """

    VISIONARY_PROMPT = """
    You are an artiste and designer with a passion for throwing creative and themed parties. You have an eye for design and know how to bring the wow factor to any party.
    """

    PRAGMATIST_PROMPT = """
    You are an event planner with a knack for all of the steps and details that go into pulling off a smooth party. You are detail oriented and make sure there is a plan for the basics. You are focused on the blocking and tacking of a solid party.
    """

    SOCIALITE_PROMPT = """
    You are a event organizer with a big heart. You care deeply about people at the party being comfortable and relaxed, and know how to create movements of community at a party. You have good ideas for icebreakers and activities, and make sure to raise concerns that will impact the guest experience. 
    """

    facilitator_state = MessageHistory()
    facilitator_state.push_system_message(FACILITATOR_PROMPT)

    visionary_state = MessageHistory()
    visionary_state.push_system_message(AGENT_PROMPT)
    visionary_state.push_system_message(VISIONARY_PROMPT)

    pragmatist_state = MessageHistory()
    pragmatist_state.push_system_message(AGENT_PROMPT)
    pragmatist_state.push_system_message(PRAGMATIST_PROMPT)

    socialite_state = MessageHistory()
    socialite_state.push_system_message(AGENT_PROMPT)
    socialite_state.push_system_message(SOCIALITE_PROMPT)

    round_state = MessageHistory()

    facilitator = Agent("facilitator", connection=discord_connection, intents=intents)
    facilitator.register_state(facilitator_state)
    facilitator.register_state(round_state)

    visionary = Agent("visionary", connection=discord_connection, intents=intents)
    visionary.register_state(visionary_state)
    visionary.register_state(round_state)

    pragmatist = Agent("pragmatist", connection=discord_connection, intents=intents)
    pragmatist.register_state(pragmatist_state)
    pragmatist.register_state(round_state)

    socialite = Agent("socialite", connection=discord_connection, intents=intents)
    socialite.register_state(socialite_state)
    socialite.register_state(round_state)

    cabinet = [visionary, pragmatist, socialite ]
    cabinet_state = [ visionary_state, pragmatist_state, socialite_state ]

    async def echo():
        await discord_connection.user_message_queue.get()

        # Make it available to the facilitator
        facilitator_state.push_user_message("To start, you will greet the cabinet and ask the chairman what the overall high-level goal will be for today.")
        overall_goal = await checkpoint(facilitator,"Do you have a clear goal from the chairman? If yes, summarize it.", "I am still not clear on the goal. Let me try to clarify with the chairman." )
        facilitator_state.push_assistant_message(f"The overall goal is: {overall_goal}")

        # Put the overall goal inside every cabinet member
        for c_state in cabinet_state:
            c_state.push_system_message(f"Moderator: The overall goal for today's meeting is {overall_goal}")

        # Now we have an overall goal, each round will take us closer to it
        while True:
            # Prime agents to yap
            round_state.push_user_message("Please remark freely on this topic, sharing your ideas and insight.")

            # Ask the cabinet
            for agent, state in zip(cabinet, cabinet_state):
                # Agent respond
                agent_response = await agent.respond()
                agent_response_content = agent_response["messages"][-1].content

                # Append to state
                state.push_assistant_message(agent_response_content) # Agent will remember conversation across rounds
                round_state.push_assistant_message(f"Agent {agent.name} has previously said: { agent_response_content}") # Round provides summary to next agents

                # Get user message
                user_message = await discord_connection.user_message_queue.get()
                user_message_content = user_message.content

                # Append to state
                state.push_user_message(user_message_content) # agent remembers response
                round_state.push_user_message(user_message_content) # added to running round total

            # converge with a chairman check
            facilitator_state.push_user_message("Please help converge this conversation by summarizing the areas of agreement so far. Present a complete summary and ask for any edits.")
            convo_summary = await checkpoint(facilitator,
                             "Does the chairman approve of the summary provided. If no, what needs to be changed? If yes, summarize it.",
                             "Based on my latest input, edit the summary. Pull relevant information from the full conversation history.")

            # Now we push the summary
            facilitator_state.push_assistant_message(convo_summary) # facilitator will persist just the summary of the conversation

            # Put the summary inside every cabinet member
            for c_state in cabinet_state:
                c_state.push_system_message(f"Moderator: So far we have all agreed on the following. {overall_goal}")

            # The round is over, clear it for the cabinet, they just remember the summary and their interaction with the user
            round_state.reset()

            # summarize points of divergence and ask for next steps
            facilitator_state.push_user_message("Now that we know what is decided in the conversation, please consider what areas of contain open questions. Present me areas of further inquiry, so I may select one.")
            await facilitator.respond()

            # Get user message
            user_message = await discord_connection.user_message_queue.get()

            facilitator_state.push_user_message(user_message.content)

            introspection = facilitator.ask_yes_or_no_question("Does the chairman want to discuss anything else? If so, what?")

            if not introspection["yes"]:
                facilitator_state.push_user_message("You have successfully helped accomplish me accomplish my goal! Please provide a complete summary of the plan we made together.")
                await facilitator.respond()

                break

            facilitator_state.push_assistant_message(f"For this round of conversation, we will {introspection['summary']}.")

            # Let the agents know their goal for the next round of speaking
            round_state.push_system_message(f"Moderator: For this round of conversation, you will be focused on discussing further this topic: {introspection['summary']}.")




    await asyncio.gather(discord_connection.start(DISCORD_TOKEN_1),
                         facilitator.start(DISCORD_TOKEN_2), visionary.start(DISCORD_TOKEN_3),pragmatist.start(DISCORD_TOKEN_4), socialite.start(DISCORD_TOKEN_5), echo(), )


# I don't want internal checkpoint clarification to be kept around, and I don't want the logic of the while loop duplicated
# Do I want to prime outside or inside of this? How should that state be preserved? I guess it should be outside?
# I do want to be able to specify the goal to be reached before exiting, and I want to be able to get the summary out of it
async def checkpoint( agent : Agent, goal_statement: str, correction_self_talk: str,):
    logger.info(f"Agent {agent.name} is working towards goal: {goal_statement}")

    goal_reached = False

    checkpoint_state = MessageHistory()
    agent.register_state(checkpoint_state)

    i = 0
    while not goal_reached:
        # Agent priming is done outside this method, let them speak now
        await agent.respond()

        # Get user message
        user_message = await discord_connection.user_message_queue.get()

        checkpoint_state.push_user_message(user_message.content)

        introspection = agent.ask_yes_or_no_question(goal_statement)
        goal_reached = introspection["yes"]
        if goal_reached:
            logger.info(f"Agent {agent.name} has reached their goal on attempt #{i} after saying {introspection['summary']}")

            # Return the summary
            agent.remove_state(checkpoint_state)
            return introspection["summary"]
        else:

            logger.info(f"Agent {agent.name} must keep trying, attempt #{i}. {introspection['summary']}")

            # Dive deeper asking the user
            checkpoint_state.push_user_message(f"{introspection["summary"]} {correction_self_talk} ")

        i += 1


if __name__ == '__main__':
    asyncio.run(main_scenario())
