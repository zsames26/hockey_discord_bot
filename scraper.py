import requests #moznost pripojit se na web a stahnout HTML
from bs4 import BeautifulSoup #vezme HTML a zpracuje do struktury

class TeamStanding: # třída reprezentuje jeden tym
    def __init__(self, rank: str, name: str, games: str, wins: str, ext_wins: str, ext_losses: str, losses: str, score: str, points: str): 
        #konstruktor, prirazuje hodnoty primo do objektu
        self.rank = rank
        self.name = name
        self.games = games
        self.wins = wins
        self.ext_wins = ext_wins
        self.ext_losses = ext_losses
        self.losses = losses
        self.score = score
        self.points = points

    def __str__(self): # magic metoda pro prevedeni objektu na text
        return f"{self.rank} {self.name} | Z: {self.games} | V: {self.wins} | VP: {self.ext_wins} | PP: {self.ext_losses} | P: {self.losses} | Skóre: {self.score} | Body: {self.points}"

class Match: #třída reprezentuje jeden zápas
    def __init__(self, teams: str, score: str, date_info: str, played: bool, won: bool = False, team_name: str = ""):
        self.teams = teams
        self.score = score
        self.date_info = date_info
        self.played = played
        self.won = won
        self.team_name = team_name

    def __str__(self):
        bold_teams = self.teams.replace(self.team_name, f"**{self.team_name}**") #vezme text soupeřů, vezme sledovaný tým a zvýrazní tučně
        if self.played:
            if self.won: #přiřadí správnou ikonu podle výhry
                icon = "✅"
            else:
                icon = "❌"
            home, away = bold_teams.split(" - ") # Rozdělení na domácí a hosty
            return f"{icon} {home} {self.score} {away} | ({self.date_info})" #odehraný zápas
        else:
            return f"📅 {bold_teams} | Termín: {self.date_info}" #neodehraný zápas

class LeagueScraper: #třída pro zisk dat z webu(zapouzdreni)
    def __init__(self):
        self.standing_url = "https://ceskyhokej.cz/competition/standings/8"
        self.headers = {"User-Agent": "Mozilla/5.0"} #zmateni nepritele 

        # Slovník všech týmů: "ZKRATKA": (ID_klubu, "Název týmu")
        self.teams = {
            "HCTUR": (81, "HC Turnov 1931"),
            "HCFRY": (83, "HC Frýdlant"),
            "HCCL":  (86, "HC Česká Lípa"),
            "TJJN":  (84, "TJ HC Jablonec n/N."),
            "LNP":   (88, "Lomnice nad Popelkou"),
            "HCSJ":  (82, "HC Stavební stroje Jičín"),
            "BKNP":  (265, "BK Nová Paka"),
            "HCVD":  (87, "HC TS Varnsdorf"),
        }

    def get_standings(self) -> list[TeamStanding]: #rika ze metoda vraci list objektu TeamStanding
        response = requests.get(self.standing_url, headers=self.headers) #pozadavek na web, zisk html a ulozeni do response
        response.raise_for_status() #kontrola, zda je server online

        soup = BeautifulSoup(response.text, "html.parser") #vezme html a rozebere ho do struktury podle HTML parseru
        table = soup.find("table", class_="table-count") # najde na strance table s tridou table-count(tam je na stance tabulka)
        tbody = table.find("tbody") # najde tbody(tam jsou vsechny teamy) v tabulce 

        standings = [] # priprava prazdneho listu
        for row in tbody.find_all("tr"): #projdou se vsechny radky (tr) v tabulce > vrati je jako seznam, ktery se prochazi for cyklem
            cols = row.find_all("td") # v kazdem radku najde vsechny sloupce (td) a ulozi je do seznamu cols
            # na strance jsou sloupce v poradi definovano v TeamStanding > pote se cisluje od 0 do 8 a ulozi se do promenne
            #.text.strip() - vezme cisty text a odstrani mezery na zacatku a konci
            rank = cols[0].text.strip()
            name = cols[1].text.strip()
            games = cols[2].text.strip()
            wins = cols[3].text.strip()
            ext_wins = cols[4].text.strip()
            ext_losses = cols[5].text.strip()
            losses = cols[6].text.strip()
            score = cols[7].text.strip()
            points = cols[8].text.strip()

            team = TeamStanding(rank, name, games, wins, ext_wins, ext_losses, losses, score, points)
            standings.append(team) # prida objekt team do listu standings na konec

        return standings # po skonceni cyklu vrati plny list standings

    # metoda prijima ciselne id a nazev tymu a vysledek bude list objektu tridy match
    def get_team_matches(self, club_id: int, team_name: str) -> list[Match]: 
        matches = []
        for page in [1, 2]: #web se rozdeluje na 2 stranky
            url = f"https://ceskyhokej.cz/competition/games/8?gameListWidget-filter%5Bclub%5D={club_id}&gameListWidget-page={page}"
            response = requests.get(url, headers=self.headers) #stahne zdroj kod stranky
            response.raise_for_status() #kdyby byl vypadek stranky

            soup = BeautifulSoup(response.text, "html.parser") # prevod HTML na strom. strukturu
            games_container = soup.find("div", id="snippet-gameListWidget-games") # vybere cast webu kde jsou zapasy

            if not games_container:
                continue
        
        # Najdeme všechny bloky jednotlivých zápasů na stránce
            for item in games_container.find_all("a", class_="game-item"): 
                #Názvy týmů
                teams_div = item.find("div", class_="team-names")
                teams = " ".join(teams_div.text.split())  # Spojíme názvy týmů do jednoho řetězce

                # Skóre zápasu
                scores = item.find_all("h6", class_="score")
                score_text = f"{scores[0].text.strip()}:{scores[1].text.strip()}"

                #U odehraného zápasu má HTML značka zápis <h6 class="score bg-blue"> proto přiřazuji odehrané zápasy díky tomu
                played = "bg-blue" in scores[0].get("class", [])

                won = False
                if played:
                    # Převedeme textové skóre na int
                    home_goals = int(scores[0].text.strip())
                    away_goals = int(scores[1].text.strip())

                    # Rozdělíme názvy týmů pomlckou a tym nalevo je domaci
                    home_team = teams.split(" - ")[0]

                    if team_name in home_team: # podle golu domacich a hostu se urcuje witez
                        won = home_goals > away_goals
                    else:
                        won = away_goals > home_goals

                # Datum a čas zápasu
                info_div = item.find("div", class_="game-info")
                paragraphs = info_div.find_all("p")
                date_info = " ".join(paragraphs[0].text.split()) if paragraphs else ""
                
                match = Match(teams, score_text, date_info, played, won, team_name)
                matches.append(match)
        return matches #vraci seznam matches s ulozenymi informacemi
    
    # najde na onlajny.com zápas daného týmu v konkrétní datum a čas
    def find_onlajny_match(self, team_name: str, date_str: str) -> tuple[str | None, str | None]: # vrací dvojici hodnot kde jsou bud str nebo nic
        url = f"https://www.onlajny.com/league/index/id/1389?date={date_str}" # url na onlajny
        response = requests.get(url, headers=self.headers) 
        response.raise_for_status()
        #stahne a převede html soubor
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("div", class_="zapasyPolozka") #najde třídu se zapasyPolozka kde jsou zapasy (kazda polozka 1 zapas)
        search_name = team_name.replace(" n/N.", "").strip() #odstraní zkratky aby to bylo stejne na onlajny.com a českém hokeji

    # projde všechny položky zápasů na stránce ligy
        for item in items: # koukne do bloku div na tridu 
            link_tag = item.find("a", class_="tymy") #vytahne ze zapasu odkaz a jmena souperu
            if not link_tag: # pojistka
                continue

    #zkontroluje zda náš hledaný tým je na odkazu
            if search_name in link_tag.text: 
                match_url = link_tag["href"] + "/type/all" #když najde hledaný tým, koukne na odkaz href a přidá koncovku /type/all ať vidíme všechny změny
                time_span = item.find("span", class_="cas") #ze třídy čas vyčte začátek zápasu
                if time_span and time_span.has_attr("content"): #jestli má time_span atribut content obsahující čas nastaví ho na start_time
                    start_time = time_span["content"] 
                else:
                    None
                return match_url, start_time

        return None, None # pokud nas tym nema zapas vyhodi none

    #stáhne skóre, stav zápasu a seznam událostí
    def get_live_matches(self, match_url: str) -> tuple[str,str,list[str]]:
        #metoda přijme urpavenou url adresu, stáhne html a převede
        response = requests.get(match_url, headers=self.headers) 
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser") 
        #aktualní skóre
        score_span = soup.find("span", class_="hlavniSkore") #vytahne ze stranky vlastni skore
        score = score_span.text.strip() #strip vždy odebere zbytečné mezery
        if score_span:
            score = score_span.text.strip()
        else:
            score = "0:0"

        status_span = soup.find("span", attrs={"data-field": "status"}) #vytáhne aktuální stav utkání (konec, 1. třetina, ...)
        if status_span:
            status = status_span.text.strip()
        else:
            status = "Neznámý stav"

        events=[]
        table = soup.find("table", class_="prubehZapasu") #najde tabulku zapasu a odfiltruje zbytecne info na strance
        if not table:
            return score, status, events
        #řádky nutné otočit protože se informace na onlajnech ukazují jako FIFO takže musíme jít nakonec abychom zjistili prvni info (chronologicky)
        rows = table.find_all("tr")
        for row in reversed(rows):
            row_classes = row.get("class", []) #pokaždé přečte řádek, přečte třídu toho řádku a vyhodnotí
            #přiřazení ikon
            if "goal" in row_classes:
                icon = "🚨"
            elif "exclusion" in row_classes:
                icon = "🟨"
            elif "time" in row_classes:
                icon = "⏱️"
            else:
                continue

            time_td = row.find("td", class_= "second") #vezme čas v události
            text_td = row.find("td", class_= "third") #vezme popis
            if not text_td:
                continue

            if time_td:
                event_time = time_td.text.strip()
            else:
                ""
            # Odstraníme případný čas poslední změny v závorce na konci 
            last_change = text_td.find("span", class_="last-change")
            if last_change:
                last_change.decompose() #odstraní z html doplňující značku
            event_text = " ".join(text_td.text.split())

            if event_time: #když se hraje
                events.append(f"{icon} **[{event_time}]** {event_text}")
            else: # začátky a konce třetin
                events.append(f"{icon} {event_text}")
        return score, status, events

#TESTY

#if __name__ == "__main__": #test na vypsání průběhu minulého zápasu pomocí url
#    scraper = LeagueScraper()
#    url = "https://www.onlajny.com/match/index/date/2026-11-21/id/552224/type/all"
#    score, status, events = scraper.get_live_matches(url)

#    print(f"Skóre: {score} | Stav: {status}")
#    print("-" * 40)
 #   for event in events:
 #       print(event)


#if __name__ == "__main__": # test na cteni url pro onlajny
#    scraper = LeagueScraper()
#    print(scraper.find_onlajny_match("HC Česká Lípa", "2026-11-07"))

#if __name__ == "__main__": #test programu, spusti je jen pri volani primo scraper.py, nebude se importovat do main.py
#   scraper = LeagueScraper()
#    for team in scraper.get_standings():
#        print(team)

#if __name__ == "__main__": #test na zapasy
#    scraper = LeagueScraper()
#    for match in scraper.get_team_matches():
#        print(match)