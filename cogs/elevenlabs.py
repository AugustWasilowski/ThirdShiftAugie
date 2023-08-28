import os
import io
import sqlite3
import uuid

import discord
from discord import FFmpegPCMAudio
from discord import option
from discord.ext import commands
import openai.error
from cogs.DatabaseCog import DatabaseCog
import requests

from cogs.flags import Flags

# SQLite Database Initialization
db_cog = DatabaseCog()
db_path = "chat_history.db"
CHUNK_SIZE = 1024

openai.api_key = os.getenv("OPENAI_API_KEY")


class ELEVENLABS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def play_audio(self, channel_id, audio_file_path):
        """Plays the given audio file in the specified voice channel."""
        channel = self.bot.get_channel(channel_id)  # Fetch the channel using the channel ID

        if not isinstance(channel, discord.VoiceChannel):  # Ensure the fetched channel is a VoiceChannel
            print(f"Channel with ID {channel_id} is not a voice channel.")
            return

        voice_client = channel.guild.voice_client

        if voice_client and voice_client.is_connected():
            voice_client.play(FFmpegPCMAudio(executable="ffmpeg", source=audio_file_path))
        else:
            print("Bot is not connected to a voice channel.")

    async def text_to_mp3(self, input_text: str, voice_id: str, channel_id: int, user_id: int, voice_channel_id: int) -> str:
        input_text = str(input_text)
        flags_cog = Flags(self.bot)
        mp3_path = None
        # Check the CanSpeak flag
        can_speak = flags_cog.get_flag("CanSpeak")
        # IF WE CAN SPEAK AND WE'RE IN A VOICE CHANNEL, THEN WE CAN SPEAK
        if can_speak:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": os.getenv("ELEVENLABS_API_KEY")
            }
            data = {
                "text": input_text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            response = requests.post(url, json=data, headers=headers)
            mp3_path = f"./outputs/{uuid.uuid4()}.mp3"

            mp3_data = b""
            with open(mp3_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        mp3_data += chunk

            db_cog.insert_chat_history(channel_id, user_id, input_text, mp3_path, mp3_data)
        else:
            db_cog.insert_chat_history(channel_id, user_id, input_text, None, None)

        await self.play_audio(voice_channel_id, mp3_path)

        return mp3_path

    async def getVoices(self, interaction: discord.Interaction):
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {
            "Accept": "application/json",
            "xi-api-key": os.getenv("ELEVENLABS_API_KEY")
        }
        response = requests.get(url, headers=headers)
        data = response.json()

        # Check if 'voices' key exists in the response
        if 'voices' in data:
            voice_data = {voice['name']: voice['voice_id'] for voice in data['voices']}
            formatted_response = "\n".join([f"{name}: {voice_id}" for name, voice_id in voice_data.items()])

            # Insert or update data in SQLite database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Create the table if not exists
            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS voices (
                        name TEXT PRIMARY KEY,
                        voice_id TEXT NOT NULL
                    );
                    """)

            # Insert or update data
            for name, voice_id in voice_data.items():
                cursor.execute("""
                        INSERT OR REPLACE INTO voices (name, voice_id)
                        VALUES (?, ?);
                        """, (name, voice_id))

            conn.commit()
            conn.close()

            await interaction.followup.send(formatted_response)
        else:
            await interaction.followup.send("No voices found in the response.")

    @discord.slash_command(name="getvoices", description="Get List of available Voices")
    async def getvoices(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.getVoices(interaction)


def setup(bot):
    bot.add_cog(ELEVENLABS(bot))
    print("Loaded Eleven Labs.")
