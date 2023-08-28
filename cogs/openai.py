import io
import os

import discord
from discord.ext import commands
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


class OPENAI(commands.Cog):
    session = None

    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="gpt4ci", description="Ask OpenAI a question")
    async def gpt4ci(self, interaction: discord.Interaction, *, message: str):
        await interaction.response.send_message(f"Generating response... to {message}")
        # await interaction.response.edit_message(view=self, content="Session Started. Generating Response")
        # await interaction.followup.send(f"Session Started. Generating Response")

        if self.session is None:
            await self.startgptsession(interaction)

        output = await self.session.generate_response(message)

        # await interaction.followup.send("Response Generated. Processing Output.")

        if len(output.files) > 0:
            await interaction.followup.send("Sending file")
            f = io.BytesIO(output.files[0].content)
            await interaction.followup.send(view=self, file=discord.File(f, filename="image.png"))
            # await interaction.followup.send(f"File Sent: {message} | {output.content}")
        else:
            await interaction.followup.send(f"{message} | {output.content}")


def setup(bot):
    bot.add_cog(OPENAI(bot))
    print("OpenAI Cog loaded")
