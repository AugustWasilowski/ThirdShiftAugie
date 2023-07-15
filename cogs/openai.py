import io
import os

from codeinterpreterapi import CodeInterpreterSession
import nextcord
from nextcord.ext import commands
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


class OPENAI(commands.Cog):
    session = None

    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="startgptsession", description="Starts a GPT Code Interpreter Session")
    async def startgptsession(self, interaction: nextcord.Interaction):
        # await interaction.response.send_message("Starting Session")
        self.session = CodeInterpreterSession()
        await self.session.astart()
        await interaction.edit_original_message(content="Session Started")

    @nextcord.slash_command(name="stopgptsession", description="Stops a GPT Code Interpreter Session")
    async def stopgptsession(self, interaction: nextcord.Interaction):
        # await interaction.response.send_message("Stopping Session")
        await self.session.astop()
        await interaction.edit_original_message(content="Session Stopped")

    @nextcord.slash_command(name="gpt4ci", description="Ask OpenAI a question")
    async def gpt4ci(self, interaction: nextcord.Interaction, *, message: str):
        await interaction.response.send_message(f"Generating response... to {message}")
        await interaction.edit_original_message(content="Session Started. Generating Response")

        if self.session is None:
            await self.startgptsession(interaction)

        output = await self.session.generate_response(message)

        await interaction.edit_original_message(content="Response Generated. Processing Output.")

        if len(output.files) > 0:
            await interaction.edit_original_message(content="Sending file")
            f = io.BytesIO(output.files[0].content)
            await interaction.edit_original_message(file=nextcord.File(f, filename="image.png"))
            await interaction.edit_original_message(content=f"File Sent: {message} | {output.content}")
        else:
            await interaction.edit_original_message(content=f"{message} | {output.content}")


def setup(bot):
    bot.add_cog(OPENAI(bot))
    print("OpenAI Cog loaded")
