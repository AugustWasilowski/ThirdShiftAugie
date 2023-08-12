import os
import io
import discord
from discord import option
from discord.ext import commands
import openai
import openai.error
import json
from cogs.DatabaseCog import DatabaseCog
from langchain.document_loaders import WebBaseLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.llms import OpenAI
from langchain.utilities import SQLDatabase

# SQLite Database Initialization
db_cog = DatabaseCog()

openai.api_key = os.getenv("OPENAI_API_KEY")


class SSA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_webquery_message(self, interaction, query, url):
        loader = WebBaseLoader(url)
        index = VectorstoreIndexCreator().from_loaders([loader])
        content = index.query(query)

        if content:
            print(content)
            # Store AI's response in the database
            db_cog.insert_chat_history(str(interaction.channel_id), 'web query', content)
            if len(content) > 2000:
                # Create a temporary file in memory
                with io.BytesIO(content.encode()) as f:
                    # Send the content as a file
                    await interaction.followup.send(file=discord.File(f, filename="response.txt"))
            else:
                await interaction.followup.send(f"{content}")
        else:
            await interaction.followup.send(f"I couldn't find an appropriate response for {query}.")

    async def process_ssa_message(self, interaction, message, personality):
        # Acknowledge the interaction if it exists
        try:
            if hasattr(interaction.response, 'defer'):
                await interaction.response.defer()
        except Exception as e:
            print(f"{e}")
            pass

        # Get the user id
        userid = "user"
        try:
            userid = str(interaction.message.author.id)
        except Exception as e:
            print(f"Error getting user id: {e}")
            pass

        db_cog.insert_chat_history(str(interaction.channel_id), userid, message)

        recent_messages = db_cog.fetch_recent_messages(str(interaction.channel_id), 10)
        messages = [{"role": "system", "content": json.dumps(db_cog.get_template(personality))}]
        messages.extend([{"role": "user", "content": msg} for msg in recent_messages])
        messages.append({"role": "user", "content": json.dumps(message)})

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages
            )
        except openai.error.APIError as e:
            # Handle API error here, e.g. retry or log
            print(f"OpenAI API returned an API Error: {e}")
            pass
        except openai.error.APIConnectionError as e:
            # Handle connection error here
            print(f"Failed to connect to OpenAI API: {e}")
            pass
        except openai.error.RateLimitError as e:
            # Handle rate limit error (we recommend using exponential backoff)
            print(f"OpenAI API request exceeded rate limit: {e}")
            pass


        content = response.choices[0].message.content

        if content:
            print(content)
            # Store AI's response in the database
            db_cog.insert_chat_history(str(interaction.channel_id), personality, content)
            if len(content) > 2000:
                # Create a temporary file in memory
                with io.BytesIO(content.encode()) as f:
                    # Send the content as a file
                    await interaction.followup.send(file=discord.File(f, filename="response.txt"))
            else:
                await interaction.followup.send(f"{content}")
        else:
            await interaction.followup.send(f"I couldn't find an appropriate response for {message}.")

    @discord.slash_command(name="ssa", description="Talk to Second Shift Augie")
    @option(
        'personality',
        str,
        description='Choose A personality type for Second Shift Augie.',
        required=False,
        choices=[
            "Second Shift Augie",
            "CLARKGPT",
            "HENRYGPT",
            "JamesGPT",
            "ELO-GPT",
            "Product Manager",
            "SVG designer",
            "Ascii Artist",
            "Rapper",
            "Pet Behaviorist"
        ]
    )
    async def ssa(self, interaction: discord.Interaction, *, message: str, personality: str = "Second Shift Augie"):
        await self.process_ssa_message(interaction, message, personality)

    @discord.slash_command(name="webquery", description="Ask questions about a website")
    @option(
        'query',
        str,
        description='Question you would like to ask about the url',
        required=True
    )
    @option(
        'URL',
        str,
        description='the URL you want to ask questions about',
        required=True
    )
    async def webquery(self, interaction: discord.Interaction, query: str, url: str):
        await interaction.response.defer()
        await self.process_webquery_message(interaction, query, url)

def setup(bot):
    bot.add_cog(SSA(bot))
    print("Loaded Second Shift Augie.")
