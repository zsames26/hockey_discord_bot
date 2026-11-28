#TESTY programu, které jsem měl na konci scraper.py, ale takto je to přehlednější
import unittest
from scraper import LeagueScraper


class TestLeagueScraper(unittest.TestCase):
    def setUp(self): #Příprava scraperu před každým testem
        self.scraper = LeagueScraper()

    def test_teams_dictionary(self): #Ověří, že slovník týmů obsahuje očekávané zkratky a názvy
        self.assertIn("HCCL", self.scraper.teams)
        self.assertEqual(self.scraper.teams["HCCL"], (86, "HC Česká Lípa"))
        self.assertEqual(self.scraper.teams["HCTUR"], (81, "HC Turnov 1931"))

    def test_find_onlajny_match_valid(self):#Ověří nalezení známého odehraného zápasu na Onlajny.com
        match_url, start_time, match_title = self.scraper.find_onlajny_match("HC Česká Lípa", "2026-11-07")
        self.assertIsNotNone(match_url)
        self.assertTrue(match_url.endswith("/type/all"))
        self.assertIsNotNone(start_time)
        self.assertIsNotNone(match_title)

    def test_find_onlajny_match_invalid_date(self):# Ověří, že pro datum bez zápasu metoda vrátí (None, None)
        match_url, start_time, match_title = self.scraper.find_onlajny_match("HC Česká Lípa", "2026-07-15")
        self.assertIsNone(match_url)
        self.assertIsNone(start_time)
        self.assertIsNone(match_title)

    def test_unique_id(self):#Ověří, že žádný tým ve slovníku nemá duplicitní ID
        ids = [team_id for team_id, _ in self.scraper.teams.values()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_get_live_matches(self):#Ověří načtení skóre a událostí z odehraného zápasu
        match_url, _, _ = self.scraper.find_onlajny_match("HC Česká Lípa", "2026-11-07")
        score, status, events = self.scraper.get_live_matches(match_url)
    
        self.assertIsNotNone(score)
        self.assertIn(status, ["Konec zápasu", "po s.n.", "po prodl."])
        self.assertGreater(len(events), 0)

    def test_team_standings(self):#Ověří, že tabulka soutěže vrátí seznam všech 8 týmů
        standings = self.scraper.get_standings()
        self.assertIsInstance(standings, list)
        self.assertEqual(len(standings), 8)

    def test_get_matches_valid_team(self):  # Ověří, že pro platný tým metoda vrátí neprázdný seznam zápasů
        matches = self.scraper.get_team_matches(86, "HC Česká Lípa")
        self.assertIsInstance(matches, list)
        self.assertGreater(len(matches), 0)

    def test_get_matches_invalid_team(self):  # Ověří, že pro neexistující ID týmu metoda vrátí prázdný seznam
        matches = self.scraper.get_team_matches(999999, "Neexistující tým")
        self.assertIsInstance(matches, list)
        self.assertEqual(len(matches), 0)
    


if __name__ == "__main__":
    unittest.main()