
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
    if bot.user in message.mentions and message.author != bot.user:
        # Store message in the database
        # db_cog.insert_chat_history(message.channel.id, message.author.id, message.content)
        print(message.content)

        ssa_instance = bot.get_cog("SSA")  # Get the SSA cog instance
        # Simulating the /ssa command behavior
        interaction = MockInteraction(message)
        await ssa_instance.process_ssa_message(interaction,
           message=message.content.replace(f'<@!{bot.user.id}>', '').strip(), personality='Second Shift Augie')
    else:
        if message.channel.type == discord.ChannelType.private and message.author != bot.user:
            print(f"Via DM: {message.content}")
            ssa_instance = bot.get_cog("SSA")  # Get the SSA cog instance
            # Simulating the /ssa command behavior
            interaction = MockInteraction(message)
            await ssa_instance.process_ssa_message(interaction,
               message=message.content.replace(f'<@!{bot.user.id}>', '').strip(), personality='Second Shift Augie')

    await bot.process_commands(message)  # Ensure other commands are still processed


load_dotenv()
GUILD_ID = os.getenv("GUILD_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Discord bot token
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Channel ID where SSA will log to.
VOICE_CHANNEL_ID = os.getenv("VOICE_CHANNEL_ID")
MOTD = "Second Shift Augie! Reporting for Duty!"


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