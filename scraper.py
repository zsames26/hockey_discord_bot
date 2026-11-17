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

class Match:
    def __init__(self, teams: str, score: str, date_info: str, played: bool, won: bool = False):
        self.teams = teams
        self.score = score
        self.date_info = date_info
        self.played = played
        self.won = won

    def __str__(self):
        if self.played:
            if self.won:
                return f"✅ {self.teams} | Výsledek: {self.score} ({self.date_info})"
            else:
                return f"❌ {self.teams} | Výsledek: {self.score} ({self.date_info})"
        else:
            return f"📅 {self.teams} | Termín: {self.date_info}"

class LeagueScraper: #třída pro zisk dat z webu(zapouzdreni)
    def __init__(self):
        self.standing_url = "https://ceskyhokej.cz/competition/standings/8"
        self.headers = {"User-Agent": "Mozilla/5.0"} #zmateni nepritele 

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

    def get_team_matches(self, club_id: int = 86, team_name: str = "HC Česká Lípa") -> list[Match]:
        matches = []
        for page in [1, 2]:
            url = f"https://ceskyhokej.cz/competition/games/8?gameListWidget-filter%5Bclub%5D={club_id}&gameListWidget-page={page}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            games_container = soup.find("div", id="snippet-gameListWidget-games")

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

                # Zda byl zápas odehrán
                played = "bg-blue" in scores[0].get("class", [])

                won = False
                if played:
                    # Převedeme textové skóre na int
                    home_goals = int(scores[0].text.strip())
                    away_goals = int(scores[1].text.strip())

                    # Rozdělíme názvy týmů 
                    home_team = teams.split(" - ")[0]

                    if team_name in home_team:
                        won = home_goals > away_goals
                    else:
                        won = away_goals > home_goals

                # Datum a čas zápasu
                info_div = item.find("div", class_="game-info")
                paragraphs = info_div.find_all("p")
                date_info = " ".join(paragraphs[0].text.split()) if paragraphs else ""
                
                match = Match(teams, score_text, date_info, played, won)
                matches.append(match)
        return matches
                                   


if __name__ == "__main__": #test programu, spusti je jen pri volani primo scraper.py, nebude se importovat do main.py
    scraper = LeagueScraper()
    for team in scraper.get_standings():
        print(team)

if __name__ == "__main__":
    scraper = LeagueScraper()
    for match in scraper.get_team_matches():
        print(match)