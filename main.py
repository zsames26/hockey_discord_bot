import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from scraper import LeagueScraper

# Načtení tokenu z .env souboru
load_dotenv()
bot_key = os.getenv('BOT_KEY')

# Nastavení práv (intents) pro čtení zpráv a reakcí
intents = discord.Intents.default()
intents.message_content = True

# Inicializace bota s prefixem "!" a nastavenými právy
bot = commands.Bot(command_prefix='!', intents=intents)

scraper = LeagueScraper()

# Události: bot vypíše zprávu po úspěšném přihlášení
@bot.event
async def on_ready():
    print(f"Přihlášen jako {bot.user}(ID: {bot.user.id})")
    print("Bot je připraven k akci!")

# Testovací přikaz: rekce na přikaz !ping
#@bot.command()
#async def ping(ctx):
#    await ctx.send("Pong!")

@bot.command() #dekorator, prikaz pro bota
async def tabulka(ctx): 
    standings = scraper.get_standings() #volani metody objektu scraper vraci list stendings
    embed = discord.Embed( 
        title="🏒 Krajská liga mužů Libereckého kraje",
        url="https://ceskyhokej.cz/competition/standings/8", 
        color=discord.Color.red()
    ) #specialni graficka tabulka (embed) nastavi nadpis, odkaz a barvu

    table_text = "```\n" #kod v discordu kde text ma stejnou sirku > zarovnani
    table_text += f"{'#':<3} {'Tým':<25} {'Z':>2} {'V':>2} {'VP':>2} {'PP':>2} {'P':>2} {'Skóre':>7} {'B':>3}\n" # vyhrazuje misto na pocet znaku
    table_text += "-" * 44 + "\n" # 44x - vypise caru

    for team in standings:
        # formatuje text na sirku predem definovanou
        table_text += f"{team.rank:<3} {team.name:<25} {team.games:>2} {team.wins:>2} {team.ext_wins:>2} {team.ext_losses:>2} {team.losses:>2} {team.score:>7} {team.points:>3}\n"

    table_text += "```" # uzavira kod
    embed.description = table_text # vloži text do embedu


    embed.set_footer(text="Zdroj: ceskyhokej.cz")  # Nastavení patičky s odkazem na zdroj
    await ctx.send(embed=embed) # odesle embed do kanalu

# Spuštění bota
if __name__ == "__main__":
    bot.run(bot_key)
