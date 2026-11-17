import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Načtení tokenu z .env souboru
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Nastavení práv (intents) pro čtení zpráv a reakcí
intents = discord.Intents.default()
intents.message_content = True

# Inicializace bota s prefixem "!" a nastavenými právy
bot = commands.Bot(command_prefix='!', intents=intents)

# Události: bot vypíše zprávu po úspěšném přihlášení
@bot.event
async def on_ready():
    print(f"Přihlášen jako {bot.user}(ID: {bot.user.id})")
    print("Bot je připraven k akci!")

# Testovací přikaz: rekce na přikaz !ping
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# Spuštění bota
if __name__ == "__main__":
    bot.run(TOKEN)
