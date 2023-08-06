import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import os
import sys
from cogs import ctxmenuhandler
from cogs import settings
from cogs.logging import get_logger
from dotenv import load_dotenv
from cogs.queuehandler import GlobalQueue

load_dotenv()
GUILD_ID = os.getenv("GUILD_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Discord bot token
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Channel ID where SSA will log to.
VOICE_CHANNEL_ID = os.getenv("VOICE_CHANNEL_ID")
MOTD = "Second Shift Augie! Reporting for Duty!"

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot.logger = get_logger(__name__)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    game = discord.Game("Use /ssa or /gpt4ci to interact.")
    await bot.change_presence(status=discord.Status.online, activity=game)
    channel = bot.get_channel(int(CHANNEL_ID))
    await channel.send(MOTD)


@bot.slash_command(name='ping', description='Get the bots latency')
async def ping(interaction: discord.Interaction):
    print('Executing ping command...')
    try:
        await interaction.send('Pong! {0}ms'.format(round(bot.latency * 1000, 1)))
    except Exception as e:
        print('An error occurred while executing the ping command:')
        print(str(e))


# stats slash command
@bot.slash_command(name='stats', description='How many images have I generated?')
async def stats(ctx):
    with open('resources/stats.txt', 'r') as f:
        data = list(map(int, f.readlines()))
    embed = discord.Embed(title='Art generated', description=f'I have created {data[0]} pictures!',
                          color=settings.global_var.embed_color)
    await ctx.respond(embed=embed)

# queue slash command
@bot.slash_command(name='queue', description='Check the size of each queue')
async def queue(ctx):
    queue_sizes = GlobalQueue.get_queue_sizes()
    description = '\n'.join([f'{name}: {size}' for name, size in queue_sizes.items()])
    embed = discord.Embed(title='Queue Sizes', description=description,
                          color=settings.global_var.embed_color)
    await ctx.respond(embed=embed)

# context menu commands
@bot.message_command(name="Get Image Info")
async def get_image_info(ctx, message: discord.Message):
    await ctxmenuhandler.get_image_info(ctx, message)


@bot.message_command(name=f"Quick Upscale")
async def quick_upscale(ctx, message: discord.Message):
    await ctxmenuhandler.quick_upscale(bot, ctx, message)


@bot.message_command(name=f"Download Batch")
async def batch_download(ctx, message: discord.Message):
    await ctxmenuhandler.batch_download(ctx, message)


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
    settings.startup_check()
    settings.files_check()

    bot.load_extension('cogs.CogLoader')
    bot.load_extension('cogs.ssa')
    bot.load_extension('cogs.openai')
    bot.load_extension('cogs.stablecog')
    bot.load_extension('cogs.settingscog')
    bot.load_extension('cogs.upscalecog')
    bot.load_extension('cogs.identifycog')
    bot.load_extension('cogs.infocog')
    bot.load_extension('cogs.generatecog')

    try:
        bot.run(os.getenv("BOT_TOKEN"))
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
