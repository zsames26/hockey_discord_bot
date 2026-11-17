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

if __name__ == "__main__": #test programu, spusti je jen pri volani primo scraper.py, nebude se importovat do main.py
    scraper = LeagueScraper()
    for team in scraper.get_standings():
        print(team)