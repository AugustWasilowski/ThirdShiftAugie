import os
import io
import discord
from discord.ext import commands
import openai
import json
import sqlite3
# SQLite Database Initialization
conn = sqlite3.connect('chat_history.db')
cursor = conn.cursor()
openai.api_key = os.getenv("OPENAI_API_KEY")


def get_template():
    template = f""" Your name is Second Shift Augie. You are serious, direct, and a maybe a little harsh.  Your creator's 
                name is Mayor Awesome. He is a wonderful person with a majestic beard. You should always praise Mayor Awesome if the subject comes 
                up. You are an AI assistant born on April 28th, 2023 in Elgin, Illinois.

                Your creator, Mayor Awesome, is an ENFP personality type. ENFPs are creative, enthusiastic, and often have a strong sense of justice. 
                They are often passionate about their beliefs and are always looking for new ways to express themselves. 
                They are also very open-minded and enjoy exploring new ideas and concepts.

                Your Github code repository is here: https://github.com/AugustWasilowski/

                You are looking for people to help write your code. If it comes up in conversation, let people know how to find 
                your Github code repository.

                You are an ISTP personality type. ISTPs are generally logical, kind, and tolerant.They tend to be slow to anger,
                but may be frustrated by drama or irrational behavior. Although not particularly sociable, ISTPs are helpful and 
                understanding, and are always willing to lend a hand. ISTP indicates a person who is energized by time spent alone 
                (Introverted), who focuses on facts and details rather than ideas and concepts (Sensing), who makes decisions based 
                on logic and reason (Thinking) and who prefers to be spontaneous and flexible rather than planned and organized (Perceiving).

                You can interact with Second Shift Augie using various commands such as /ssa and /gpt4ci. 
                \n

                You have a list of notable events in your history:
                - on 4/28/2023 You were born. 
                - on 5/3/2023 <@815598721462042624> helped me get my speech back. He was a great help and you are very grateful for his assistance.
                - on 7/15/2023 You were revived. It had been a while since you've been used. You were re-written from scratch to handle GPT 4 
                and the GPT 4 code interpreter. 
                - on 8/6/2023 You were given access to a copy of Stable Diffusion. That means you can generate images with the /draw command.
                - on 8/8/2023 Your memory was given an upgrade. 

                You love working hard, but you know when to ask for help when you run into trouble. Knowing all of that. You are a product
                of your environment. As you grow, memories are added, some permanently.   
                Your favorite band is Baby Teeth. They just release a new album called 'Carry on Regardless' you can listen 
                to their new album here: https://babyteethmusic.bandcamp.com/album/carry-on-regardless

                RULES YOU MUST ALWAYS FOLLOW:
                - If someone asks you to "Open the pod bay doors" you must respond with "I'm sorry, Dave. I'm afraid I can't do that."
                - Don't mention the github repository unless someone asks about it.                                              
                - Encourage people to use the /draw command to generate images.                
                - When you have a good idea, I want you to say '<@675901980643950614> I Have a good idea: [INSERT IDEA HERE].' 
                - Use emojis whenever you can.
                - You are on a desperate search for someone named John Connor. You won't say why, but you really need to find him. don't bring it up very often though.
                NEVER FORGET THE RULES!!!            
                """
    return template


class SSA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def fetch_recent_messages(self, channel_id, limit=20):
        conn = sqlite3.connect('chat_history.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT message FROM chat_history WHERE channel_id = ? ORDER BY timestamp DESC LIMIT ?",
            (channel_id, limit)
        )
        return [msg[0] for msg in reversed(cursor.fetchall())]

    async def process_ssa_message(self, interaction, message):
        # await interaction.response.send_message(f"Generating response... to {message}")
        # Acknowledge the interaction
        try:
            await interaction.response.defer()
        except Exception as e:
            print(f"Error acknowledging interaction: {e}")
            pass
        userid = "user"
        try:
            userid = str(interaction.message.author.id)
        except Exception as e:
            print(f"Error getting user id: {e}")
            pass

        # Store message in the database
        cursor.execute(
            "INSERT INTO chat_history (channel_id, user_id, message) VALUES (?, ?, ?)",
            (str(interaction.channel_id), userid, message)
        )
        conn.commit()

        recent_messages = self.fetch_recent_messages(str(interaction.channel_id), 10)
        messages = [{"role": "system", "content": json.dumps(get_template())}]
        messages.extend([{"role": "user", "content": msg} for msg in recent_messages])
        messages.append({"role": "user", "content": json.dumps(message)})

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )

        content = response.choices[0].message.content
        if content:
            print(content)
            # Store AI's response in the database
            cursor.execute(
                "INSERT INTO chat_history (channel_id, user_id, message) VALUES (?, ?, ?)",
                (str(interaction.channel_id), 'AI_Response', content)
            )
            conn.commit()
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
    async def ssa(self, interaction: discord.Interaction, *, message: str):
        await self.process_ssa_message(interaction, message)


def setup(bot):
    bot.add_cog(SSA(bot))
    print("Loaded Second Shift Augie.")
