import os
import sqlite3
import discord
from discord import option
from discord.ext import commands
import openai.error
from cogs.DatabaseCog import DatabaseCog

db_cog = DatabaseCog()
db_path = "chat_history.db"
CHUNK_SIZE = 1024

openai.api_key = os.getenv("OPENAI_API_KEY")
DATABASE_NAME = "chat_history.db"
voice_mapping = {
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
    "Clyde": "2EiwWnXFnvU5JabPnv8n",
    "Domi": "AZnzlk1XvdvUeBnXmlld",
    "Dave": "CYw3kZ02Hs0563khs1Fj",
    "Fin": "D38z5RcWu1voky8WS1ja",
    "Bella": "EXAVITQu4vr4xnSDxMaL",
    "Antoni": "ErXwobaYiN019PkySvjV",
    "Thomas": "GBv7mTt0atIp3Br8iCZE",
    "Charlie": "IKne3meq5aSn9XLyUdCD",
    "Emily": "LcfcDJNUP1GQjkzn1xUU",
    "Elli": "MF3mGyEYCl7XYWbV9V6O",
    "Callum": "N2lVS1w4EtoT3dr4eOWO",
    "Patrick": "ODq5zmih8GrVes37Dizd",
    "Harry": "SOYHLrjzK2X1ezoPC6cr",
    "Liam": "TX3LPaxmHKxFdv7VOQHJ",
    "Dorothy": "ThT5KcBeYPX3keUQqHPh",
    "Josh": "TxGEqnHWrfWFTfGW9XjX",
    "Arnold": "VR6AewLTigWG4xSOukaG",
    "Charlotte": "XB0fDUnXU5powFXDhCwa",
    "Matilda": "XrExE9yKIg1WjnnlVkGX",
    "Matthew": "Yko7PKHZNXotIFUBG7I9",
    "James": "ZQe5CZNOzWyzPSCn5a3c",
    "Joseph": "Zlb1dXrM653N07WRdFW3",
    "Jeremy": "bVMeCyTHy58xNoL34h3p",
    "Michael": "flq6f7yk4E4fJM5XTYuZ",
    "Ethan": "g5CIjZEefAph4nQFvHAz",
    "Gigi": "jBpfuIE2acCO8z3wKNLl",
    "Freya": "jsCqWAovK2LkecY7zXl4",
    "Grace": "oWAxZDx7w5VEj9dCyTzz",
    "Daniel": "onwK4e9ZLuTAKqWW03F9",
    "Serena": "pMsXgVXv3BLzUgSXRplE",
    "Adam": "pNInz6obpgDQGcFmaJgB",
    "Nicole": "piTKgcLEGmPE4e6mEKli",
    "Jessie": "t0jbNlBVZ17f02VDIeMI",
    "Ryan": "wViXBPUzp2ZZixB1xQuM",
    "Sam": "yoZ06aMxZJJ28mfd3POQ",
    "Glinda": "z9fAnlkpzviPz146aGWa",
    "Giovanni": "zcAOhNBS3c14rBihAFp1",
    "Mimi": "zrHiDhphv9ZnVXBqCLjz",
    "Oprah": "2TYWQ2w9gFlqc0tkQgBB",
    "Ricky": "9BMdhkMpc0YWMDBgnbH5",
    "Announcer": "B7gyDJMtib1sqKks5PKw",
    "Empire": "EqBpDbTVZLX8HrE9dSLM",
    "Joe": "GDU2Ht22DuUmAWaPBizB",
    "Ron B": "LqRudPMP6PD7L1janNvt",
    "Yelly Jack": "NfYfGHwfwcVsm91xZtnJ",
    "David": "SGgIzzop9KRjR4GpeauC",
    "Ron": "SRcsStpANwza7YQ9Yaj1",
    "Donald G": "UzIoG9wfOTjN4yCoinyw",
    "Walter": "WiVdDMVLkYuBJ4IuTTvj",
    "Martha": "XmfquPMN5uOLxP5BRSvn",
    "Howie": "eABApCkTYb96J1PzkQve",
    "Antonio": "fLBqoBPZ52gzWrceAFqp",
    "Ken": "j274W1HcoIbtI6JW67ih",
    "Laura": "jlVXy69fdEliJtlLCkP6",
    "John": "oS6Z0ysvZJrNWL7c7v3M",
    "William": "qzaIfzrA32MuHlBc1BKi",
    "August": "sXr0HJbPWGGDVPwm88Bz",
    "Steve": "ysXcYaOWGqoMH5TlYin8"
}


class Flags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.initialize_database()

    def initialize_database(self):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # Create the Flags table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Flags (
                name TEXT PRIMARY KEY,
                value BOOLEAN
            )
            """)

        # Check if the "CanSpeak" flag exists
        cursor.execute("SELECT value FROM Flags WHERE name = 'CanSpeak'")
        flag = cursor.fetchone()

        # If the "CanSpeak" flag doesn't exist, insert it with a value of FALSE
        if not flag:
            cursor.execute("INSERT INTO Flags (name, value) VALUES (?, ?)", ("CanSpeak", False))

        conn.commit()
        conn.close()

    def set_flag(self, flag_name, value):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute("INSERT OR REPLACE INTO Flags (name, value) VALUES (?, ?)", (flag_name, value))
        conn.commit()
        conn.close()

    def get_flag(self, flag_name):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM Flags WHERE name = ?", (flag_name,))
        flag_value = cursor.fetchone()

        conn.close()
        return flag_value[0] if flag_value else None

    def delete_flag(self, flag_name):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM Flags WHERE name = ?", (flag_name,))
        conn.commit()
        conn.close()

    @discord.slash_command(name="flags", description="Second Shift Augie's Flags and Settings")
    @option(
        'canspeak',
        str,
        description='Can Second Shift Augie speak?',
        required=True,
        choices=[
            "Yes",
            "No"
        ]
    )
    async def ssavoice(self, interaction: discord.Interaction, canspeak: str = "No"):
        self.set_flag("CanSpeak", True if canspeak == "Yes" else False)
        await interaction.response.send_message(f"Flag 'CanSpeak' set to {'True' if canspeak == 'Yes' else 'False'}")

    @discord.slash_command(name="setvoice", description="Set the voice")
    @option(
        name="voice",
        description="Choose a voice",
        required=True,
        choices=[{'name': str(name), 'value': str(voice_id)} for name, voice_id in voice_mapping.items()]
    )
    async def set_voice(self, interaction: discord.Interaction, voice: str):
        selected_voice_id = voice_mapping[voice]
        self.set_flag("voice", selected_voice_id)
        await interaction.response.send_message(f"Voice set to {voice} with ID {selected_voice_id}")
        input_text = f"Voice set to {voice}"

        channel_id = interaction.channel_id
        user_id = interaction.user.id
        voice_channel_id = interaction.guild.get_member(user_id).voice.channel.id

        await self.bot.get_cog("ELEVENLABS").text_to_mp3(input_text, selected_voice_id, channel_id, user_id, voice_channel_id)


def setup(bot):
    bot.add_cog(Flags(bot))
    print("Loaded Flags.")
