# WoW-recruitment

Beta-Skript für Raider.IO und WoWProgress.

Das Skript sucht Spieler, die gerade eine Gilde suchen, und speichert sie als
CSV-Liste. Die Liste lässt sich mit Excel öffnen. So muss niemand die
Suchseiten von Hand durchklicken.

## Feste Suchregeln

Diese Regeln gelten immer und für beide Quellen:

- **nur DPS**
- **nur deutschsprachige Spieler** (German)
- **nur Gesuche, die jünger als 48 Stunden sind**

## Quellen und Ergebnisse

| Quelle | Wann | Ergebnisdatei |
|---|---|---|
| Raider.IO | immer | `raiderio_recruitment.csv` |
| WoWProgress | nur in der erweiterten Version (Auswahl 2) | `wowprogress_recruitment.csv` |

Die Dateien landen im selben Ordner wie das Skript.

## Voraussetzungen

- Windows
- **Python 3.8 oder neuer** von <https://www.python.org/downloads/>
  Beim Installieren den Haken bei **„Add python.exe to PATH“** setzen.
- Internetverbindung

Alles Weitere (Playwright und den Browser) installiert die Start-Datei selbst.

## Starten

1. Im Ordner `RaiderIo` doppelt auf **`Start.bat`** klicken.
2. Beim ersten Start werden die Bibliotheken installiert. Das dauert ein paar Minuten.
3. Auswahl treffen:
   - **1** = nur Raider.IO
   - **2** = Raider.IO + WoWProgress (erweiterte Version)
4. Ein Browserfenster öffnet sich. Das Cookie-Banner **wegklicken**.
   Das Skript wartet dafür 25 Sekunden (bei WoWProgress noch einmal 15 Sekunden).
   Das Fenster nicht schließen, das Skript arbeitet darin.
5. Wenn in der Konsole „Fertig.“ steht, liegen die CSV-Dateien im Ordner.

Ab dem zweiten Start entfällt die Installation, und das Cookie-Banner ist meist schon bestätigt.

### Starten ohne Start-Datei (z. B. in PyCharm)

```bash
pip install -r requirements.txt
python -m playwright install chromium

python raiderio_recruitment_scraper.py                # nur Raider.IO
python raiderio_recruitment_scraper.py --wowprogress  # + WoWProgress
```

## Spalten der Ergebnislisten

**`raiderio_recruitment.csv`**

| Spalte | Bedeutung |
|---|---|
| `character_name` | Name des Charakters |
| `realm`, `region` | Server und Region |
| `wow_class` | Klasse |
| `guild` | aktuelle Gilde (falls vorhanden) |
| `ilvl` | Itemlevel |
| `availability` | Raidzeiten |
| `published` | Alter des Gesuchs (z. B. `9m`, `3h`, `1d`) |
| `discord`, `twitch`, `battletag`, `contact_raw` | Kontaktdaten aus dem Profil |
| `profile_url` | Link zum Raider.IO-Profil |

**`wowprogress_recruitment.csv`**

| Spalte | Bedeutung |
|---|---|
| `character_name`, `realm`, `region` | Name, Server, Region |
| `wow_class`, `specs` | Klasse und gespielte Specs |
| `guild`, `ilvl` | aktuelle Gilde, Itemlevel |
| `languages`, `raids_per_week` | Sprachen, gewünschte Raidtage pro Woche |
| `published` | letzte Aktualisierung (z. B. `12 hours ago`) |
| `battletag` | Battletag |
| `profile_url` | Link zum WoWProgress-Profil |

## Einstellungen

Oben im Skript im Abschnitt `KONFIGURATION`:

| Einstellung | Standard | Bedeutung |
|---|---|---|
| `MAX_AGE_HOURS` | `48` | Gesuche ab diesem Alter (in Stunden) werden ignoriert |
| `CLASSES` | `[]` | Klassenfilter, z. B. `["Mage", "Rogue"]`; leer = alle Klassen |
| `MANUAL_WAIT_SECONDS` | `25` | Wartezeit für das Cookie-Banner bei Raider.IO |
| `WOWPROGRESS_WAIT_SECONDS` | `15` | Wartezeit für das Cookie-Banner bei WoWProgress |
| `MAX_PAGES` | `10` | höchstens so viele Ergebnisseiten |
| `FETCH_CONTACT_INFO` | `True` | Kontaktdaten aus den Raider.IO-Profilen holen |
| `CONTACT_LIMIT` | `5` | nur die ersten N Raider.IO-Profile besuchen (`0` = alle) |

`ROLE = "dps"` und `REGION = "german"` sind feste Regeln und sollen nicht geändert werden.

## So arbeitet das Skript

1. **Raider.IO:** Es öffnet die erweiterte Suche, gefiltert auf DPS und German,
   neueste Gesuche zuerst. Es liest Seite für Seite aus und hört auf, sobald
   ein Gesuch 48 Stunden oder älter ist. Danach holt es für die ersten
   Profile die Kontaktdaten.
2. **WoWProgress:** Es öffnet die „Looking for Guild“-Liste (Sprache Deutsch,
   neueste zuerst) und liest sie bis zur 48-Stunden-Grenze aus. Danach öffnet
   es jedes Profil und prüft:
   - **Sprache:** Steht eine Sprache im Profil, muss German dabei sein.
   - **Rolle:** Die zuerst genannte Spec darf kein Tank oder Heiler sein.
     Steht keine Spec im Profil, zählen nur reine DPS-Klassen
     (Hunter, Mage, Rogue, Warlock).

## Ordnerinhalt

| Datei/Ordner | Inhalt | Weitergeben? |
|---|---|---|
| `raiderio_recruitment_scraper.py` | das Skript | ja |
| `Start.bat` | Start per Doppelklick | ja |
| `requirements.txt` | benötigte Bibliotheken | ja |
| `README.md` | diese Anleitung | ja |
| `_python_umgebung/` | Python-Umgebung der Start-Datei | nein |
| `.venv/` | Python-Umgebung von PyCharm | nein |
| `_browserprofil/` | Cookies und Zustimmungen des Browsers | nein |
| `*.csv` | Ergebnislisten | nein |

## Häufige Probleme

**„Python wurde nicht gefunden.“**
Python installieren und dabei „Add python.exe to PATH“ anhaken. Danach `Start.bat` neu starten.

**„Datei ist gesperrt (in Excel offen?)“**
Die CSV ist noch in Excel geöffnet. Das Skript speichert dann unter einem neuen
Namen mit Datum, z. B. `raiderio_recruitment_2026-11-10_00-30.csv`.
Nichts geht verloren. Beim nächsten Mal Excel vorher schließen.

**WoWProgress findet keine Einträge.**
Meist steht im Browserfenster eine Sicherheitsprüfung. Beim nächsten Lauf
schneller wegklicken oder `WOWPROGRESS_WAIT_SECONDS` erhöhen.

**Installation hängt oder bricht ab.**
Den Ordner `_python_umgebung` löschen und `Start.bat` neu starten.
Dann wird alles frisch installiert.

## Hinweise

- **Beta:** Raider.IO und WoWProgress haben keine offizielle Schnittstelle dafür.
  Das Skript liest die Webseiten aus. Ändern die Seiten ihren Aufbau, kann das
  Auslesen fehlschlagen.
- Der WoWProgress-Teil wurde noch nicht auf der echten Seite getestet.
- Die Pausen zwischen den Seitenaufrufen (`DELAY_PAGE`, `DELAY_PROFILE`)
  schonen die Server. Bitte nicht auf 0 setzen.
