import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from scraper import LeagueScraper
import asyncio
from datetime import datetime
from discord.ext import tasks

# Načtení tokenu z .env souboru
load_dotenv()
bot_key = os.getenv('BOT_KEY')

# Nastavení práv (intents) pro čtení zpráv a reakcí
intents = discord.Intents.default()
intents.message_content = True

# Inicializace bota s prefixem "!" a nastavenými právy
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

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

@bot.command(aliases=["HCTUR", "HCFRY", "HCCL", "TJJN", "LNP", "HCSJ", "BKNP", "HCVD"]) #prida prikaz matches a k nemu pripoji 8 zkratek => vsechny spousti stejnou fci
async def matches(ctx):
    cmd = ctx.invoked_with.upper()  # Získání názvu příkazu, který byl vyvolán (rozumí i malým písmenům)

    if cmd not in scraper.teams: #při !matches vypise text
        await ctx.send("Zadej zkratku konkrétního týmu: `!HCTUR`, `!HCFRY`, `!HCCL`, `!TJJN`, `!LNP`, `!HCSJ`, `!BKNP`, `!HCVD`")
        return
    
    club_id, team_name = scraper.teams[cmd] # vytahne informace o tymu (id a nazev) 
    matches = scraper.get_team_matches(club_id, team_name)  # Získání zápasů pro tým 
    #vypis odehranych a budoucich zapasu hccl
    embed = discord.Embed(
        title=f"🏒 Zápasy: {team_name}",
        url=f"https://ceskyhokej.cz/competition/games/8?gameListWidget-filter%5Bclub%5D={club_id}",
        color=discord.Color.blue()
    )
    #prazdne promenne
    played_text= ""
    upcoming_text = ""
    #projde zapasy, pokud se odehrali pridaji se do played_text jinak do upcoming_text
    for m in matches: # vezme zapas pojmenuje ho m, vyhodnoti jestli byl odehrany nebo nadchazejici
        if m.played:
            played_text += f"{m}\n"
        else:
            upcoming_text += f"{m}\n"

    #pridani dvou poli do embedu
    embed.add_field(
        name="📊 Odehrané zápasy",
        value=played_text if played_text else "Zatím žádné odehrané zápasy.",
        inline=False
    )
    embed.add_field(
        name="📅 Nadcházející zápasy",
        value=upcoming_text if upcoming_text else "Žádné naplánované zápasy.",
        inline=False
    )

    embed.set_footer(text="Zdroj: ceskyhokej.cz")
    await ctx.send(embed=embed) #odesle hotovou kartu

# Proměnné pro uchování stavu živého přenosu
live_channel = None
live_url = None
live_team = None
sent_events = set() #ukládání událostí
wait_task = None #odkaz na běžící úkol na pozadí

#smyčka na pozadí co každých 120 s kontroluje stav zápasu
@tasks.loop(seconds=120)
async def live_tracker():
    if not live_channel or not live_url:
        return

    score, status, events = scraper.get_live_matches(live_url) #přečte ze stránky info a porovná
    new_messages = []
    #aby neposílal stejné info 2x
    for event in events:
        if event not in sent_events:
            sent_events.add(event)
            new_messages.append(event)
    #když přijde nová událost pošle na discord zprávy po dávkách (discord má limit)
    if new_messages:
        chunk = f"**🏒 {live_team} | Stav: {status} | Skóre: {score}**\n"
        for msg in new_messages:
            if len(chunk) + len(msg) + 2 > 1900:
                await live_channel.send(chunk)
                chunk = ""
            chunk += f"{msg}\n"
        if chunk:
            await live_channel.send(chunk)

    #když zápas už je u konce ukončí smyčku
    if any("Konec zápasu" in e for e in events):
        await live_channel.send(f"🏁 **Přenos utkání ({live_team}) byl automaticky ukončen.**")
        live_tracker.stop()


# Spuštění bota
if __name__ == "__main__":
    bot.run(bot_key)
