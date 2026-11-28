# Hockey Discord Bot – Krajská liga mužů (Liberecký kraj)

Discord bot pro sledování **Krajské ligy mužů Libereckého kraje**. Bot je naprogramován v pythonu. Automaticky stahuje aktuální tabulku soutěže, rozpis odehraných i budoucích zápasů z webu Českého hokeje (`ceskyhokej.cz`) a umožňuje živé textové sledování utkání včetně gólů a vyloučení z portálu `onlajny.com`.

---

## Hlavní funkce

* **Aktuální tabulka soutěže:** Zobrazení pořadí týmů, odehraných zápasů, skóre a bodů.
* **Rozpis zápasů týmů:** Výpis minulých výsledků i nadcházejících utkání pro všechny týmy soutěže.
* **Živé sledování utkání:**
  * Automatické vyhledání zápasu na `onlajny.com` podle zkratky týmu a data.
  * *Čekání na start:* Pokud zápas ještě nezačal, bot se uspí až do začátku zápasu a poté přenos sám spustí.
  * Pravidelná kontrola událostí každých 120 sekund (góly, asistence, vyloučení, začátky a konce třetin) bez opakování již odeslaných zpráv.
  * Automatické ukončení přenosu po skončení utkání (nebo ruční zastavení přes `!stoplive`).
* **Nápověda (`!help`):** Karta se seznamem všech příkazů a zkratek týmů.

---

## Dostupné příkazy

| Příkaz | Popis | Příklad použití |
| :--- | :--- | :--- |
| `!!tabulka` | Zobrazí aktuální tabulku Krajské ligy mužů. | `!tabulka` |
| `!matches` | Vypíše zkratky týmů pro rozpis zápasů daného týmu. | `!matches` |
| `!<ZKRATKA>` | Vypíše rozpis zápasů vybraného týmu. | `!HCCL` |
| `!live <ZKRATKA> [YYYY-MM-DD]` | Spustí živé sledování zápasu (bez data hledá dnešní zápas). | `!live HCCL` nebo `!live HCCL 2026-11-07` |
| `!stoplive` | Ručně zastaví probíhající živé sledování nebo čekání na zápas. | `!stoplive` |
| `!help` | Zobrazí nápovědu a seznam zkratek týmů. | `!help` |

---

## Zkratky týmů

| Zkratka | Název týmu |
| :--- | :--- |
| `HCTUR` | HC Turnov 1931 |
| `HCFRY` | HC Frýdlant |
| `HCCL` | HC Česká Lípa |
| `TJJJN` | TJ HC Jablonec n/N. |
| `LNP` | Lomnice nad Popelkou |
| `HCSJ` | HC Stavební stroje Jičín |
| `BKNP` | BK Nová Paka |
| `HCVD` | HC TS Varnsdorf |

---

## Struktura projektu

* `main.py` – Hlavní soubor Discord bota (obsluha příkazů, formátování zpráv, časování a smyčka živého přenosu na pozadí).
* `scraper.py` – Modul pro stahování a parsování HTML dat z webů `ceskyhokej.cz` a `onlajny.com` pomocí knihoven `requests` a `BeautifulSoup4`.
* `requirements.txt` – Seznam potřebných knihoven třetích stran.
* `.env` – Konfigurační soubor obsahující tajný Discord token (`BOT_KEY`), který není součástí repozitáře (je uveden v `.gitignore`).

---

## Instalace a spuštění

1. **Naklonování repozitáře:**
   ```
   git clone https://github.com/zsames26/hockey-discord-bot.git
   cd hockey-discord-bot
   ```

## Vytvoření a nastavení účtu v Discord Developer Portal

Před spuštěním bota je nutné vytvořit aplikaci v Discord Developer Portalu a získat přístupový token:

1. **Vytvoření aplikace:**
   * Na stránkách [Discord Developer Portal](https://discord.com/developers/applications)
   * **New Application** => **Create**.
2. **Získání tokenu a zapnutí Intents:**
   * V levém menu záložka **Bot**.
   * Kliknout na **Reset Token**, zkopírovat vygenerovaný token a ulož si ho (do souboru `.env`).
   * Níže do sekce **Privileged Gateway Intents** a zapnout **Message Content Intent** (nutné pro čtení příkazů `!`), poté **Save Changes**.
3. **Pozvání bota na server:**
   * V levém menu do **OAuth2** => **URL Generator**.
   * V sekci **Scopes** zaškrtnout **`bot`**.
   * V sekci **Bot Permissions** zaškrtnout `View Channels`, `Send Messages`, `Embed Links` a `Read Message History`.
   * Zkopírovat vygenerovaný odkaz, otevřít ho v prohlížeči a přidat bota na Discord server.


## Postup
1. **Vytvoření a aktivace virtuálního prostředí:**
    ```
    python -m venv venv
    source venv/bin/activate
    ```
2. **Instalace závislostí:**
    ```
    pip install -r requirements.txt
    ```
3. **Nastavení tokenu bota:**
    ```
    BOT_KEY=<vas_discord_token>
    ```
4. **Spuštění bota**
    ```
    python main.py
    ```
