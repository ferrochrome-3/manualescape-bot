import os
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from dotenv import load_dotenv

# environment variables so the token isnt hardcoded
load_dotenv()
TOKEN = os.getenv('MANUALESCAPE_TOKEN')

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# what servers to sync in because global sync is slow
# i made it global sync anyways because it wasnt working
GUILD_IDS = [
     1541255195437170840,
     1375357349425971231,
     1493444917211697192
]

# unenroll command
@bot.tree.command(name="unenroll", description="Unenroll your chromebook via ManualEscape")
# input fields for sn and cookie
@app_commands.describe(
    serial="Your device's serial number",
    oauth="The OAuth cookie's contents that you got from devtools"
)
async def run_slash(interaction: discord.Interaction, serial: str, oauth: str):
    await interaction.response.defer(ephemeral=True) 

    proc = await asyncio.create_subprocess_exec(
        "python3", "manualescape.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdin_data = f"{serial}\n{oauth}\n".encode()
    stdout, stderr = await proc.communicate(stdin_data)

# output thingy 
    if proc.returncode != 0:
        await interaction.followup.send(
            f"Script failed with the following error:\n```{stderr.decode()[:1900]}```", ephemeral=True
        )
        return

    await interaction.followup.send(f"```{stdout.decode()[:1900]}```", ephemeral=True)

# what it does when the bot starts :brian:
@bot.event
async def on_ready():
    for guild_id in GUILD_IDS:
        guild = discord.Object(id=guild_id)
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync()

    print(f"Cleared and re-synced commands as {bot.user}")

bot.run(TOKEN)
