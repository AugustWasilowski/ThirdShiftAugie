import os
from codeinterpreterapi import CodeInterpreterSession
import nextcord
from nextcord.ext import commands
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


class OPENAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="gpt4ci", description="Ask OpenAI a question")
    async def gpt4ci(self, interaction: nextcord.Interaction, *, message: str):
        session = CodeInterpreterSession()
        await session.astart()
        output = await session.generate_response(message)

        if output.files[0].content:
            await interaction.response.send_message(file=nextcord.File(output.files[0].content, filename="image.png"))
        else:
            await interaction.response.send_message(output.text)

        if output.content:
            await interaction.resp.send_message(output.content)

        await session.astop()


def setup(bot):
    bot.add_cog(OPENAI(bot))
    print("OpenAI Cog loaded")
