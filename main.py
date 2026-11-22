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
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None, case_insensitive=True)
scraper = LeagueScraper()

# Události: bot vypíše zprávu po úspěšném přihlášení
@bot.event
async def on_ready():
    print(f"Přihlášen jako {bot.user}(ID: {bot.user.id})")
    print("Bot je připraven k akci!")
    for guild in bot.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    await channel.send("🏒 Ahoj, jsem online! Napiš `!help` a zjisti, co všechno umím.")
                    break

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

#časovač na pozadí a jeho přerušení
async def wait_and_start(wait_seconds: float):
    try: #hlídá jestli nebylo nějaké přerušení
        await asyncio.sleep(wait_seconds) #přeruší chod na wait_seconds ať může dělat cokoli jiného
        if live_channel and live_team and live_url: #pojistka, ověří zda má vše potřebné o zápase
            await live_channel.send(f"🔴 **Spouštím živé sledování:** {live_team}\n🔗 {live_url}")
            live_tracker.start()
    except asyncio.CancelledError:
        # Tento blok se spustí, když uživatel čekání zruší přes !stoplive
        pass


# spustí živé sledování zápasu
@bot.command()
async def live(ctx, team_shortcut: str = "", date_str: str = ""):
    global live_channel, live_url, live_team, sent_events, wait_task

    if live_tracker.is_running() or (wait_task and not wait_task.done()): #zkontroluje jestli už neběží sledování
        await ctx.send(f"⚠️ Už právě sleduji tým **{live_team}**. Nejprve použij `!stoplive`.")
        return

    cmd = team_shortcut.upper() #pokud není volaný jaký tým hodí to pomocnou hlášku
    if cmd not in scraper.teams:
        await ctx.send("Zadej zkratku týmu a volitelně datum (YYYY-MM-DD), např. `!live HCCL 2026-11-07`.")
        return

    # Pokud uživatel nezadal datum, dosadí se automaticky dnešní
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    _, team_name = scraper.teams[cmd] #ze slovoníku vezme podle zkratky id a název tým, "_" udává že nepotřebujeme id 
    await ctx.send(f"🔍 Hledám zápas týmu **{team_name}** pro datum **{date_str}**...")

    match_url, start_time_str = scraper.find_onlajny_match(team_name, date_str) #vytáhne si url a čas zápasu

    if not match_url: #pokud metoda zápas nenašla vyhodí chybovou hlášku
        await ctx.send(f"❌ Pro tým **{team_name}** nebyl v den **{date_str}** nalezen žádný zápas na Onlajny.com.")
        return
    # Nastavení globálních proměnných pro nový přenos
    live_channel = ctx.channel
    live_url = match_url
    live_team = team_name
    sent_events = set()

    if start_time_str:
        start_dt = datetime.fromisoformat(start_time_str) #převede text z html na objekt 
        now_dt = datetime.now() 
        wait_seconds = (start_dt - now_dt).total_seconds() #odečte od začátku čas a převede na sekundy

        if wait_seconds > 0: #pokud je rozdíl kladný zápas ještě není
            minutes = int(wait_seconds // 60)
            await ctx.send(f"⏳ Zápas **{team_name}** začíná v **{start_dt.strftime('%H:%M')}**. Čekám ({minutes} min) a pak se automaticky zapnu!")
            wait_task = asyncio.create_task(wait_and_start(wait_seconds)) #bot čeká na pozadí a nebude tak zablokovaný při čekání
            return

    await ctx.send(f"🔴 **Spouštím živé sledování:** {team_name}\n🔗 {match_url}")
    live_tracker.start()

#ruční zastavení živého sledování
@bot.command()
async def stoplive(ctx):
    global wait_task

    if live_tracker.is_running(): #pokud už zápas běží
        live_tracker.stop()
        await ctx.send("🛑 Živé sledování bylo ručně zastaveno.")
    elif wait_task and not wait_task.done(): #když zápas ještě nezačal a bot čeká
        wait_task.cancel()
        wait_task = None
        await ctx.send(f"🛑 Plánované čekání na zápas týmu **{live_team}** bylo zrušeno.")
    else:
        await ctx.send("ℹ️ Momentálně neběží žádné živé sledování.")

#Zobrazí přehled všech příkazů bota a seznam zkratek týmů
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="🏒 Nápověda – Krajská liga mužů (Liberecký kraj)",
        description="Přehled dostupných příkazů a zkratek jednotlivých týmů:",
        color=discord.Color.blue()
    )

    #Sekce se seznamem příkazů
    commands_text = (
        "**`!tabulka`**\n"
        "Zobrazí aktuální tabulku soutěže.\n\n"
        "**`!matches`**\n"
        "Vypíše zkratky týmů pro které chceme zjistit zápasy.\n\n"
        "**`!<zkratka>`**\n"
        "Vypíše rozpis zápasů daného týmu při volání zkratky.\n"
        "Př.: !hccl nebo !HCCL\n\n"
        "**`!live <ZKRATKA> [YYYY-MM-DD]`**\n"
        "Spustí živé sledování zápasu (bez data hledá dnešní zápas) nebo vypíše průběh již odehraného utkání.\n"
        "Př.: !live hccl nebo !live HCCL 2026-11-07\n\n"
        "**`!stoplive`**\n"
        "Ručně zastaví probíhající živé sledování nebo čekání na zápas.\n\n"
        "**`!help`**\n"
        "Zobrazí tuto nápovědu."
    )
    embed.add_field(name="📋 Příkazy", value=commands_text, inline=False)
    teams_lines = []

    for shortcut, (_, team_name) in scraper.teams.items(): #vybere z týmů zkratku a název týmu
        teams_lines.append(f"**`{shortcut}`** – {team_name}")

    teams_text = "\n".join(teams_lines)
    embed.add_field(name="🛡️ Zkratky týmů", value=teams_text, inline=False)

    await ctx.send(embed=embed)

# Spuštění bota
if __name__ == "__main__":
    bot.run(bot_key)
