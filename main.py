
from dotenv import load_dotenv
import asyncio
import os
import sys
from cogs import settings
from cogs.logging import get_logger
from cogs.queuehandler import GlobalQueue
import discord
from discord.ext import commands

from cogs.DatabaseCog import DatabaseCog
db_cog = DatabaseCog()

# Create the database table if it doesn't already exist
db_cog.create_table()

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot.logger = get_logger(__name__)

load_dotenv()
GUILD_ID = os.getenv("GUILD_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Discord bot token
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Channel ID where SSA will log to.
VOICE_CHANNEL_ID = os.getenv("VOICE_CHANNEL_ID")
MOTD = "Second Shift Augie! Reporting for Duty!"
print(f"bot token {BOT_TOKEN}")

class MockInteraction:
    def __init__(self, message):
        self.message = message
        self.channel_id = message.channel.id
        self.user_id = message.author.id
        self.response = self.Response(message)
        self.followup = self.Followup(message)

    class Response:
        def __init__(self, message):
            self.message = message

        async def send_message(self, content):
            await self.message.channel.send(content)

    class Followup:
        def __init__(self, message):
            self.message = message

        async def send(self, content=None, *, file=None):
            if file:
                # If a file is provided, send the file using the original channel object
                await self.message.channel.send(file=file)
            else:
                await self.message.channel.send(content)


@bot.event
async def on_message(message):
    # If the bot is mentioned and the message isn't from the bot itself
    ssa_instance = bot.get_cog("ssa")  # Get the SSA cog instance

    if not ssa_instance:
        print("SSA instance not found")
        return

    if bot.user in message.mentions and message.author != bot.user:
        # Store message in the database
        # db_cog.insert_chat_history(message.channel.id, message.author.id, message.content)
        print(message.content)

        # Simulating the /ssa command behavior
        interaction = MockInteraction(message)
        await ssa_instance.process_ssa_message(interaction,
           message=message.content.replace(f'<@!{bot.user.id}>', '').strip(), personality='Second Shift Augie')
    else:
        if message.channel.type == discord.ChannelType.private and message.author != bot.user:
            print(f"Via DM: {message.content}")

            # Simulating the /ssa command behavior
            interaction = MockInteraction(message)
            await ssa_instance.process_ssa_message(interaction,
               message=message.content.replace(f'<@!{bot.user.id}>', '').strip(), personality='Second Shift Augie')

    await bot.process_commands(message)  # Ensure other commands are still processed




@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    game = discord.Game("Use /ssa or /gpt4ci to interact.")
    await bot.change_presence(status=discord.Status.online, activity=game)
    channel = bot.get_channel(int(CHANNEL_ID))
    await channel.send(MOTD)


# @bot.slash_command(name='ping', description='Get the bots latency')
# async def ping(interaction: discord.Interaction):
    #     print('Executing ping command...')
    # try:
    #         await interaction.send('Pong! {0}ms'.format(round(bot.latency * 1000, 1)))
    # except Exception as e:
    #         print('An error occurred while executing the ping command:')
#        print(str(e))


# stats slash command
# @bot.slash_command(name='stats', description='How many images have I generated?')
# async def stats(ctx):
    #   with open('resources/stats.txt', 'r') as f:
    #   data = list(map(int, f.readlines()))
    # embed = discord.Embed(title='Art generated', description=f'I have created {data[0]} pictures!',
    #                           color=settings.global_var.embed_color)
    # await ctx.respond(embed=embed)


# queue slash command
# @bot.slash_command(name='queue', description='Check the size of each queue')
# async def queue(ctx):
    #     queue_sizes = GlobalQueue.get_queue_sizes()
    # description = '\n'.join([f'{name}: {size}' for name, size in queue_sizes.items()])
    # embed = discord.Embed(title='Queue Sizes', description=description,
    #                     color=settings.global_var.embed_color)
    # await ctx.respond(embed=embed)



@bot.event
async def on_ready():
    bot.logger.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='user commands'))
    for guild in bot.guilds:
        print(f"I'm active in {guild.id} a.k.a {guild}!")


# fallback feature to delete generations if aiya has been restarted
@bot.event
async def on_raw_reaction_add(ctx):
    if ctx.emoji.name == '❌':
        try:
            end_user = f'{ctx.user_id}'
            message = await bot.get_channel(ctx.channel_id).fetch_message(ctx.message_id)
            if end_user in message.content and "Queue" not in message.content:
                await message.delete()
            # this is for deleting outputs from /identify
            if message.embeds:
                if message.embeds[0].footer.text == f'{ctx.member.name}#{ctx.member.discriminator}':
                    await message.delete()
        except(Exception,):
            # so console log isn't spammed with errors
            pass


@bot.event
async def on_guild_join(guild):
    print(f'Wow, I joined {guild.name}!')


async def shutdown(bot):
    await bot.close()


if __name__ == '__main__':
    # settings.startup_check()
    # settings.files_check()
    print("BEGIN LOAD COGS")
    bot.load_extension('cogs.flags')
    bot.load_extension('cogs.CogLoader')
    bot.load_extension('cogs.ssa')
    bot.load_extension('cogs.openai')
    # bot.load_extension('cogs.stablecog')
    # bot.load_extension('cogs.settingscog')
    # bot.load_extension('cogs.upscalecog')
    # bot.load_extension('cogs.identifycog')
    # bot.load_extension('cogs.infocog')
    # bot.load_extension('cogs.generatecog')
    bot.load_extension('cogs.elevenlabs')
    print("END LOAD COGS")

    try:
        print(f"logging in with {BOT_TOKEN}")
        bot.run(BOT_TOKEN)
    except KeyboardInterrupt:
        bot.logger.info('Keyboard interrupt received. Exiting.')
        asyncio.run(shutdown(bot))
    except SystemExit:
        bot.logger.info('System exit received. Exiting.')
        asyncio.run(shutdown(bot))
    except Exception as e:
        bot.logger.error(e)
        asyncio.run(shutdown(bot))
    finally:
        sys.exit(0)


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

from cogs.flags import Flags

# SQLite Database Initialization
db_cog = DatabaseCog()

openai.api_key = os.getenv("OPENAI_API_KEY")


class ssa(commands.Cog):
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

        recent_messages = db_cog.fetch_recent_messages(str(interaction.channel_id), 30)
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
            if len(content) > 2000:
                # Create a temporary file in memory
                with io.BytesIO(content.encode()) as f:
                    # Send the content as a file
                    await interaction.followup.send(file=discord.File(f, filename="response.txt"))
            else:
                elevenlabs_cog = self.bot.get_cog("ELEVENLABS")
                if elevenlabs_cog:  # Check if the ELEVENLABS cog is loaded
                    flags = Flags(self.bot)
                    voice_id = flags.get_flag("voice")
                    channel_id = interaction.channel_id
                    try:
                        user_id = interaction.user_id
                    except AttributeError:
                        user_id = interaction.user.id

                    try:
                        voice_channel_id = interaction.message.author.voice.channel.id
                        mp3_path = await elevenlabs_cog.text_to_mp3(content, voice_id, channel_id, user_id, voice_channel_id)
                        print(mp3_path)
                    except AttributeError:
                        print("Author has no voice channel")
                        voice_channel_id = None
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
            "Ascii Artist",
            "Rapper",
            "Pet Behaviorist",
            "AI Developer"
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

    @discord.slash_command(name="joinvoice", description="Join A Voice Channel")
    async def joinvoice(self, interaction: discord.Interaction):
        member = interaction.user  # Get the member who invoked the command

        if member.voice and member.voice.channel:
            channel = member.voice.channel
            await channel.connect()
            await interaction.response.send_message(f"Joined {channel.name}!")
            input_text = f"Second Shift Augie, reporting for duty!"
            flags = Flags(self.bot)
            voice_id = flags.get_flag("voice")
            channel_id = interaction.channel_id
            user_id = interaction.user.id
            voice_channel_id = interaction.guild.get_member(user_id).voice.channel.id

            await self.bot.get_cog("ELEVENLABS").text_to_mp3(input_text, voice_id, channel_id, user_id,
                                                             voice_channel_id)
        else:
            await interaction.response.send_message("You are not connected to a voice channel!")


def setup(bot):
    bot.add_cog(ssa(bot))
    print("Loaded Second Shift Augie.")
