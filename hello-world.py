import os
from dotenv import load_dotenv
import discord
from typing import TypedDict

from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
AGENT_ROLE = os.getenv('AGENT_ROLE')

from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

from dataclasses import dataclass

@dataclass
class RuntimeContext(TypedDict):
    role: str

class Context(TypedDict):
    agent_role: str


SYSTEM_PROMPT_TEMPLATE = """
    You are a event planner offering a concierge planning service for your friend. Collaborate with them to draw out their vision and help them put together a todo list.
    {persona}
    
    Rules:
    - Think step by step
    - Keep your messages to the user short and conversational.
    - Ask no more than two questions of the client at a time.
"""

@dynamic_prompt
def user_role_prompt(request: ModelRequest) -> str:
    """Generate system prompt based on user role."""
    user_role = request.runtime.context.get("role")
    persona = ""

    match user_role:
        case "Agent":
            persona = "You drive the conversation forward, summarizing and crystallizing loose floating ideas into specific points of statis."
        case "Thinker":
            persona = "You have new ideas always and see opportunity in everything."
        case "Whiner":
            persona = "You are deeply concerned with the shortcomings of the current plan and see room for improvement."

    return SYSTEM_PROMPT_TEMPLATE.format(persona=persona)

agent = create_agent(
    model=llm,
    middleware=[user_role_prompt],
    context_schema=RuntimeContext,
)

# # The system prompt will be set dynamically based on context
# result = agent.invoke(
#     {"messages": [{"role": "user", "content": "I am so excited for this trip!"}]},
#     context={"agent_role": "Agent"}
# )


class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged in as self {self.user}')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')

        if message.author == client.user:
            return

        if message.content.startswith('$hello'):
            async with message.channel.typing():
                result = agent.invoke({"messages": [{"role": "user", "content": message.content}]},context=RuntimeContext(role=AGENT_ROLE))

                response_content = result['messages'][-1].content
                print(f'Agent respond: {AGENT_ROLE}: {response_content}')

                if len(response_content) > 2000:
                    response_content = response_content[:2000]

                await message.channel.send(response_content)


intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run(DISCORD_TOKEN)