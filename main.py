import nextcord
import os
from nextcord.ext import commands
from dotenv import load_dotenv

load_dotenv()
GUILD_ID = os.getenv("GUILD_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Discord bot token
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Channel ID where SSA will log to.
VOICE_CHANNEL_ID = os.getenv("VOICE_CHANNEL_ID")
MOTD = "Second Shift Augie! Reporting for Duty!"

intents = nextcord.Intents().all()
bot = commands.Bot(command_prefix='!', intents=nextcord.Intents.all())



@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    game = nextcord.Game("/ssa works now.")
    await bot.change_presence(status=nextcord.Status.online, activity=game)
    channel = bot.get_channel(int(CHANNEL_ID))
    await channel.send(MOTD)


@bot.slash_command(name='ping', description='Get the bots latency')
async def ping(interaction: nextcord.Interaction):
    print('Executing ping command...')
    try:
        await interaction.send('Pong! {0}ms'.format(round(bot.latency * 1000, 1)))
    except Exception as e:
        print('An error occurred while executing the ping command:')
        print(str(e))


if __name__ == '__main__':
    bot.load_extension('cogs.CogLoader')
    bot.load_extension('cogs.ssa')
    bot.load_extension('cogs.openai')
    bot.run(os.getenv("BOT_TOKEN"))
