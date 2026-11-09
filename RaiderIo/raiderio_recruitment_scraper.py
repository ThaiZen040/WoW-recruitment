"""
raiderio_recruitment_scraper.py   (Version 6)
==============================================
Sucht Spieler, die eine Gilde suchen, und exportiert sie als CSV.

Feste Regeln (gelten für alle Quellen):
  - nur DPS
  - nur deutschsprachige Spieler (German)
  - nur Gesuche, die jünger als 48 Stunden sind

Quellen:
  - Raider.IO   -> raiderio_recruitment.csv   (immer)
  - WoWProgress -> wowprogress_recruitment.csv (erweiterte Version)

STARTEN (für alle): Doppelklick auf "Start.bat" im selben Ordner.
Die Start-Datei installiert beim ersten Mal alles Nötige selbst.

Starten von Hand (z. B. in PyCharm):
    python raiderio_recruitment_scraper.py                -> nur Raider.IO
    python raiderio_recruitment_scraper.py --wowprogress  -> + WoWProgress

So läuft es ab:
Beim Start öffnet sich ein Browserfenster. Klick dort einmal das
Cookie-/Consent-Banner weg. Das Skript wartet dafür (MANUAL_WAIT_SECONDS)
und macht danach automatisch weiter. Die Zustimmung wird in einem
Browserprofil gespeichert, beim nächsten Lauf entfällt der Klick meist.
"""

# Erlaubt moderne Typangaben wie "float | None" auch in älteren
# Python-Versionen (ab 3.8). Muss ganz oben stehen.
from __future__ import annotations

import csv
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright


# ===========================================================================
# KONFIGURATION
# ===========================================================================

# Rolle: fest auf DPS. Es wird IMMER nur nach DPS gesucht.
# (Bewusst nicht mehr umstellbar, damit niemand aus Versehen Heiler/Tanks holt.)
ROLE = "dps"

# Nur Gesuche, die jünger als so viele Stunden sind, kommen in die Liste.
MAX_AGE_HOURS = 48

# Klassenfilter. [] = alle Klassen.
#   "Death Knight", "Demon Hunter", "Druid", "Evoker", "Hunter", "Mage",
#   "Monk", "Paladin", "Priest", "Rogue", "Shaman", "Warlock", "Warrior"
CLASSES = []

# Region: fest auf "german". Es werden IMMER nur deutsche Spieler gesucht.
REGION = "german"

# Sekunden, die du Zeit bekommst, um das Consent-Banner wegzuklicken.
# Beim zweiten Lauf kannst du das auf 5 senken.
MANUAL_WAIT_SECONDS = 25

# Dasselbe für WoWProgress (eigene Seite, eigenes Cookie-Banner).
WOWPROGRESS_WAIT_SECONDS = 15

# Sicherheitsgrenze: höchstens so viele Ergebnisseiten durchblättern.
# Normalerweise stoppt das Skript vorher von selbst, sobald die
# Einträge älter als MAX_AGE_HOURS werden.
MAX_PAGES = 10

# Kontaktdaten aus den einzelnen Raider.IO-Profilen holen?
FETCH_CONTACT_INFO = True

# Nur die ersten N Raider.IO-Profile besuchen (0 = alle).
CONTACT_LIMIT = 5

DELAY_PAGE = 3.0
DELAY_PROFILE = 1.5

# Ordner, in dem dieses Skript liegt. Alle Dateien landen hier.
BASE_DIR = Path(__file__).parent

OUTPUT_CSV = BASE_DIR / "raiderio_recruitment.csv"
WOWPROGRESS_CSV = BASE_DIR / "wowprogress_recruitment.csv"

# Hier speichert der Browser Cookies und Zustimmung zwischen den Läufen.
PROFILE_DIR = BASE_DIR / "_browserprofil"

# WoWProgress-Liste "Looking for Guild": nur Deutsch (lang=de),
# sortiert nach letzter Aktualisierung (sortby=ts, neueste zuerst).
WOWPROGRESS_URL = "https://www.wowprogress.com/gearscore/?lfg=1&lang=de&sortby=ts"

# Erweiterte Version an/aus. Wird beim Start "--wowprogress" mitgegeben
# (das macht Start.bat bei Auswahl 2), ist der Wert True.
RUN_WOWPROGRESS = "--wowprogress" in sys.argv


# ===========================================================================
# RAIDER.IO
# ===========================================================================

def build_search_url(role: str, region: str) -> str:
    url = (
        "https://raider.io/search?type=character"
        f"&recruitment.guild_raids.main_character.main_roles[0][eq]={role}"
        "&recruitment.guild_raids.main_character.mainspec_ids[0][eq]="
        "&recruitment.guild_raids.main_character.offspec_ids[0][eq]="
        "&recruitment.guild_raids.schedule[0][eq][day]="
        "&recruitment.guild_raids.schedule[0][eq][startTime]="
        "&recruitment.guild_raids.schedule[0][eq][endTime]="
        "&recruitment.guild_raids.profile.published_at[0][gte]=0"
    )
    if region:
        url += f"&region[0][eq]={region}"
    url += "&sort[recruitment.guild_raids.profile.published_at]=desc"
    return url


WOW_CLASSES = [
    "Death Knight", "Demon Hunter", "Druid", "Evoker", "Hunter", "Mage",
    "Monk", "Paladin", "Priest", "Rogue", "Shaman", "Warlock", "Warrior",
]


EXTRACT_ROWS_JS = r"""
() => {
  const baseKey = (href) => {
    const m = (href || '').match(/\/characters\/([^\/]+)\/([^\/\?#]+)\/([^\/\?#]+)/);
    if (!m) return null;
    if (m[3].toLowerCase() === 'recruitment') return null;
    return (m[1] + '/' + m[2] + '/' + m[3]).toLowerCase();
  };

  const links = Array.from(document.querySelectorAll('a[href*="/characters/"]'))
    .filter(a => baseKey(a.getAttribute('href')));

  const byChar = new Map();
  for (const a of links) {
    const key = baseKey(a.getAttribute('href'));
    if (!byChar.has(key)) byChar.set(key, []);
    byChar.get(key).push(a);
  }

  const out = [];
  for (const [key, charLinks] of byChar.entries()) {
    let el = charLinks[0];
    let row = charLinks[0];
    for (let i = 0; i < 10 && el.parentElement; i++) {
      el = el.parentElement;
      const distinct = new Set(
        Array.from(el.querySelectorAll('a[href*="/characters/"]'))
          .map(a => baseKey(a.getAttribute('href'))).filter(Boolean)
      );
      if (distinct.size > 1) break;
      row = el;
    }

    const m = key.match(/^([^\/]+)\/([^\/]+)\/(.+)$/);
    const href = charLinks[0].getAttribute('href') || '';
    const clean = href.replace(/\/recruitment\/?$/, '');

    const lines = (row.innerText || '')
      .split('\n').map(s => s.replace(/\s+/g, ' ').trim()).filter(Boolean);

    const hints = Array.from(row.querySelectorAll('img, span, i, div, svg, use'))
      .map(e => [
        e.getAttribute('alt') || '', e.getAttribute('title') || '',
        e.getAttribute('data-tooltip') || '', e.getAttribute('aria-label') || '',
        e.getAttribute('class') || '', e.getAttribute('src') || '',
        e.getAttribute('href') || ''
      ].join(' ')).join(' ');

    const guildLink = row.querySelector('a[href*="/guilds/"]');

    out.push({
      key: key,
      region: m ? m[1].toUpperCase() : '',
      realm: m ? m[2] : '',
      character_name: (charLinks[0].innerText || '').trim() ||
                      decodeURIComponent(m ? m[3] : ''),
      profile_url: clean.startsWith('http') ? clean : 'https://raider.io' + clean,
      guild: guildLink ? (guildLink.innerText || '').trim() : '',
      lines: lines,
      hints: hints
    });
  }
  return out;
}
"""


def detect_class(raw: dict) -> str:
    hay = (raw.get("hints", "") + " " + " ".join(raw.get("lines", []))).lower()
    for cls in WOW_CLASSES:
        variants = {cls.lower(), cls.lower().replace(" ", "-"),
                    cls.lower().replace(" ", "_"), cls.lower().replace(" ", "")}
        if any(v in hay for v in variants):
            return cls
    return ""


def published_to_hours(published: str) -> float | None:
    # Wandelt die Altersangabe von raider.io in Stunden um.
    # "9m" = 9 Minuten, "3h" = 3 Stunden, "1d" = 1 Tag, "2w" = 2 Wochen.
    m = re.fullmatch(r"(\d+)([mhdw])", published or "")
    if not m:
        return None
    zahl = int(m.group(1))
    einheit = m.group(2)
    stunden_pro_einheit = {"m": 1 / 60, "h": 1, "d": 24, "w": 24 * 7}
    return zahl * stunden_pro_einheit[einheit]


def parse_row(raw: dict) -> dict:
    lines = raw.get("lines", [])
    joined = " | ".join(lines)

    ilvl = ""
    m = re.search(r"\b(\d{3}\.\d{1,2})\b", joined)
    if m:
        ilvl = m.group(1)

    published = ""
    m = re.search(r"\b(\d+\s*[hdwm])\b(?!\w)", joined)
    if m:
        published = m.group(1).replace(" ", "")

    availability = ""
    m = re.search(r"(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})", joined)
    if m:
        availability = m.group(1)
    elif re.search(r"multiple times", joined, re.I):
        availability = "Multiple Times"

    name = raw.get("character_name", "").strip() or raw.get("key", "").split("/")[-1]

    return {
        "character_name": name,
        "realm": raw.get("realm", ""),
        "region": raw.get("region", ""),
        "wow_class": detect_class(raw),
        "guild": raw.get("guild", ""),
        "ilvl": ilvl,
        "availability": availability,
        "published": published,
        "profile_url": raw.get("profile_url", ""),
        "discord": "", "twitch": "", "battletag": "", "contact_raw": "",
    }


EXTRACT_CONTACT_JS = r"""
() => {
  let box = null;
  const all = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,div,span,p,strong'));
  for (const el of all) {
    const t = (el.textContent || '').trim();
    if (/^contact\s*info$/i.test(t)) {
      let p = el.parentElement;
      for (let i = 0; i < 6 && p; i++) {
        if ((p.innerText || '').trim().length > t.length + 2) { box = p; break; }
        p = p.parentElement;
      }
      if (box) break;
    }
  }
  if (!box) return { raw: '', links: [], hints: '' };

  const raw = (box.innerText || '').replace(/contact\s*info/i, '').trim();
  const links = Array.from(box.querySelectorAll('a'))
    .map(a => a.getAttribute('href') || '').filter(Boolean);
  const hints = Array.from(box.querySelectorAll('img, svg, i, span, use'))
    .map(e => [e.getAttribute('alt') || '', e.getAttribute('title') || '',
               e.getAttribute('class') || '', e.getAttribute('src') || '',
               e.getAttribute('href') || ''].join(' ')).join(' | ');
  return { raw: raw, links: links, hints: hints };
}
"""

def parse_contact(data: dict) -> dict:
    data = data or {}
    raw = data.get("raw", "") or ""
    links = data.get("links", []) or []

    result = {"discord": "", "twitch": "", "battletag": "", "contact_raw": ""}

    for href in links:
        low = href.lower()
        handle = href.rstrip("/").split("/")[-1]
        if "discord" in low and not result["discord"]:
            result["discord"] = handle
        elif "twitch" in low and not result["twitch"]:
            result["twitch"] = handle
        elif "battle.net" in low and not result["battletag"]:
            result["battletag"] = handle

    m = re.search(r"\b([A-Za-z0-9À-ſ]{2,20}#\d{3,6})\b", raw)
    if m and not result["battletag"]:
        result["battletag"] = m.group(1)

    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if lines and not result["discord"]:
        result["discord"] = lines[0]
    if len(lines) > 1 and not result["twitch"]:
        result["twitch"] = lines[1]

    result["contact_raw"] = " / ".join(lines)
    return result


def click_next(page) -> bool:
    for loc in (page.get_by_role("button", name=re.compile(r"^\s*next\s*$", re.I)),
                page.get_by_role("link", name=re.compile(r"^\s*next\s*$", re.I)),
                page.locator("button:has-text('Next')"),
                page.locator("a:has-text('Next')")):
        try:
            if loc.count() == 0:
                continue
            el = loc.first
            if not el.is_visible():
                continue
            try:
                if el.is_disabled():
                    return False
            except Exception:
                pass
            el.click()
            return True
        except Exception:
            continue
    return False


def scrape_raiderio(page) -> list[dict]:
    search_url = build_search_url(ROLE, REGION)
    print("#" * 70)
    print("RAIDER.IO")
    print("#" * 70)

    rows_by_key: dict[str, dict] = {}

    page.goto(search_url, wait_until="domcontentloaded", timeout=60000)

    print("=" * 70)
    print(f">>> Browserfenster ist offen. Klick das Cookie-Banner weg,")
    print(f">>> falls eins da ist. Ich warte {MANUAL_WAIT_SECONDS} Sekunden ...")
    print("=" * 70)
    time.sleep(MANUAL_WAIT_SECONDS)

    for page_no in range(1, MAX_PAGES + 1):
        time.sleep(DELAY_PAGE)

        try:
            raw_rows = page.evaluate(EXTRACT_ROWS_JS)
        except Exception as e:
            print(f"Seite {page_no}: Auslesen fehlgeschlagen ({e})")
            raw_rows = []

        new_count = 0
        too_old_reached = False
        for raw in raw_rows:
            parsed = parse_row(raw)

            # Die Liste ist nach Datum sortiert (neueste zuerst).
            # Sobald ein Eintrag zu alt ist, sind alle danach auch zu alt.
            hours = published_to_hours(parsed["published"])
            if hours is not None and hours >= MAX_AGE_HOURS:
                too_old_reached = True
                break

            key = raw.get("key") or parsed["profile_url"]
            if key and key not in rows_by_key:
                rows_by_key[key] = parsed
                new_count += 1

        print(f"Seite {page_no}: {len(raw_rows)} Eintraege, {new_count} neu "
              f"(gesamt {len(rows_by_key)})")

        if too_old_reached:
            print(f"Eintraege aelter als {MAX_AGE_HOURS} Std. erreicht - Ende.")
            break
        if page_no >= MAX_PAGES:
            break
        if not click_next(page):
            print("Kein weiterer 'Next'-Button - Ende der Ergebnisse.")
            break
        try:
            page.wait_for_timeout(2500)
        except Exception:
            pass

    results = list(rows_by_key.values())

    if CLASSES:
        wanted = {c.strip().lower() for c in CLASSES}
        before = len(results)
        unknown = sum(1 for r in results if not r["wow_class"])
        results = [r for r in results if r["wow_class"].lower() in wanted]
        print(f"\nKlassenfilter: {before} -> {len(results)} "
              f"({unknown} ohne erkannte Klasse verworfen)")

    if FETCH_CONTACT_INFO and results:
        targets = results if CONTACT_LIMIT == 0 else results[:CONTACT_LIMIT]
        print(f"\nHole Kontaktdaten fuer {len(targets)} Profile ...")
        for i, row in enumerate(targets, start=1):
            try:
                page.goto(row["profile_url"], wait_until="domcontentloaded", timeout=45000)
                time.sleep(DELAY_PROFILE)
                row.update(parse_contact(page.evaluate(EXTRACT_CONTACT_JS)))
                print(f"  [{i}/{len(targets)}] {row['character_name']}-{row['realm']}: "
                      f"{row['contact_raw'] or 'keine Angabe'}")
            except Exception as e:
                print(f"  [{i}/{len(targets)}] {row['character_name']}: Fehler ({e})")

    return results


# ===========================================================================
# WOWPROGRESS (erweiterte Version)
# ===========================================================================

# Spezialisierungen, die NICHT DPS sind. Alles andere zählt als DPS.
# (Die Namen sind eindeutig: "Holy" ist bei Paladin UND Priester ein Heiler,
#  "Protection" bei Paladin UND Krieger ein Tank.)
TANK_SPECS = {"blood", "vengeance", "guardian", "brewmaster", "protection"}
HEALER_SPECS = {"restoration", "holy", "discipline", "mistweaver", "preservation"}

# Klassen, die NUR DPS spielen können. Steht im Profil keine Spec,
# reicht bei diesen Klassen die Klasse selbst als Nachweis.
PURE_DPS_CLASSES = {"Hunter", "Mage", "Rogue", "Warlock"}


# Liest die Zeilen der WoWProgress-Tabelle aus. Jede Zeile hat einen Link
# auf "/character/<region>/<realm>/<name>".
WOWPROGRESS_ROWS_JS = r"""
() => {
  const out = [];
  const seen = new Set();
  for (const a of document.querySelectorAll('a[href*="/character/"]')) {
    const href = a.getAttribute('href') || '';
    const m = href.match(/\/character\/([^\/]+)\/([^\/]+)\/([^\/\?#]+)/);
    if (!m) continue;
    const tr = a.closest('tr');
    if (!tr) continue;
    const key = (m[1] + '/' + m[2] + '/' + m[3]).toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    const guild = tr.querySelector('a[href*="/guild/"]');
    out.push({
      key: key,
      region: m[1].toUpperCase(),
      realm: decodeURIComponent(m[2]),
      character_name: (a.innerText || '').replace(/\(lfg\)/i, '').trim()
                      || decodeURIComponent(m[3]),
      guild: guild ? (guild.innerText || '').trim() : '',
      profile_url: href.startsWith('http') ? href : 'https://www.wowprogress.com' + href,
      text: (tr.innerText || '').replace(/\s+/g, ' ').trim()
    });
  }
  return out;
}
"""


def ago_to_hours(text: str) -> float | None:
    # Wandelt WoWProgress-Angaben wie "12 hours ago", "1 day ago",
    # "a day ago" oder "3 weeks ago" in Stunden um.
    m = re.search(r"\b(\d+|an?)\s+(minute|hour|day|week|month|year)s?\s+ago\b",
                  text or "", re.I)
    if not m:
        return None
    zahl_text = m.group(1).lower()
    # "a day ago" bzw. "an hour ago" bedeutet 1.
    zahl = 1 if zahl_text in ("a", "an") else int(zahl_text)
    einheit = m.group(2).lower()
    stunden_pro_einheit = {"minute": 1 / 60, "hour": 1, "day": 24,
                           "week": 24 * 7, "month": 24 * 30, "year": 24 * 365}
    return zahl * stunden_pro_einheit[einheit]


def parse_wowprogress_row(raw: dict) -> dict:
    text = raw.get("text", "")

    ilvl = ""
    m = re.search(r"\b(\d{3}\.\d{2})\b", text)
    if m:
        ilvl = m.group(1)

    published = ""
    m = re.search(r"\b((?:\d+|an?)\s+(?:minute|hour|day|week|month|year)s?\s+ago)\b",
                  text, re.I)
    if m:
        published = m.group(1)

    return {
        "character_name": raw.get("character_name", ""),
        "realm": raw.get("realm", ""),
        "region": raw.get("region", ""),
        "wow_class": "", "specs": "", "languages": "", "raids_per_week": "",
        "guild": raw.get("guild", ""),
        "ilvl": ilvl,
        "published": published,
        "battletag": "",
        "profile_url": raw.get("profile_url", ""),
    }


def parse_wowprogress_profile(text: str) -> dict:
    # Holt aus dem Text der Charakterseite die Angaben des LFG-Profils.
    def field(label: str) -> str:
        m = re.search(label + r"\s*:\s*(.+)", text, re.I)
        return m.group(1).strip() if m else ""

    battletag = ""
    m = re.search(r"\b([A-Za-z0-9À-ſ]{2,20}#\d{3,6})\b", text)
    if m:
        battletag = m.group(1)

    # Klasse: In der Kopfzeile steht z. B. "human warlock 80" (Rasse, Klasse,
    # Stufe). Wir suchen eine Klasse, auf die direkt eine Zahl folgt.
    # So wird nicht aus Versehen ein Menüpunkt oder Gildenname erkannt.
    wow_class = ""
    klassen_muster = "|".join(c.lower() for c in WOW_CLASSES)
    m = re.search(r"\b(" + klassen_muster + r")\s+\d{1,2}\b", text, re.I)
    if m:
        wow_class = m.group(1).title()

    return {
        "wow_class": wow_class,
        "specs": field("Specs playing"),
        "languages": field("Languages"),
        "raids_per_week": field("Raids per week"),
        "battletag": battletag,
    }


def is_dps(row: dict) -> bool | None:
    # True = DPS, False = kein DPS, None = nicht feststellbar.
    specs = row.get("specs", "")
    if specs:
        # Die zuerst genannte Spec gilt als Hauptspec.
        # "Fire, Frost" -> "fire"
        main = re.split(r"[,/|]", specs)[0].strip().lower()
        # Nur das erste Wort, falls z. B. "Holy (Paladin)" dasteht.
        main = main.split(" ")[0] if main else ""
        if main:
            return main not in TANK_SPECS and main not in HEALER_SPECS
    if row.get("wow_class") in PURE_DPS_CLASSES:
        return True
    return None


def scrape_wowprogress(page) -> list[dict]:
    print("\n" + "#" * 70)
    print("WOWPROGRESS")
    print("#" * 70)

    rows_by_key: dict[str, dict] = {}

    page.goto(WOWPROGRESS_URL, wait_until="domcontentloaded", timeout=60000)
    print("=" * 70)
    print(f">>> WoWProgress ist offen. Klick das Cookie-Banner weg, falls")
    print(f">>> eins da ist. Ich warte {WOWPROGRESS_WAIT_SECONDS} Sekunden ...")
    print("=" * 70)
    time.sleep(WOWPROGRESS_WAIT_SECONDS)

    # --- Schritt 1: Liste durchblättern, bis die Einträge zu alt sind ---
    for page_no in range(1, MAX_PAGES + 1):
        time.sleep(DELAY_PAGE)
        try:
            raw_rows = page.evaluate(WOWPROGRESS_ROWS_JS)
        except Exception as e:
            print(f"Seite {page_no}: Auslesen fehlgeschlagen ({e})")
            raw_rows = []

        new_count = 0
        too_old_reached = False
        for raw in raw_rows:
            parsed = parse_wowprogress_row(raw)
            hours = ago_to_hours(parsed["published"])
            if hours is not None and hours >= MAX_AGE_HOURS:
                too_old_reached = True
                break
            if raw["key"] not in rows_by_key:
                rows_by_key[raw["key"]] = parsed
                new_count += 1

        print(f"Seite {page_no}: {len(raw_rows)} Eintraege, {new_count} neu "
              f"(gesamt {len(rows_by_key)})")

        if not raw_rows:
            print("Keine Eintraege gefunden. Steht im Browser eine Sicherheits-"
                  "pruefung? Dann beim naechsten Lauf schneller wegklicken.")
            break
        if too_old_reached:
            print(f"Eintraege aelter als {MAX_AGE_HOURS} Std. erreicht - Ende.")
            break
        if page_no >= MAX_PAGES:
            break
        # WoWProgress hat einen Link "next >" zum Weiterblättern.
        nxt = page.get_by_role("link", name=re.compile(r"^\s*next", re.I))
        if nxt.count() == 0:
            print("Kein 'next'-Link - Ende der Ergebnisse.")
            break
        nxt.first.click()
        page.wait_for_timeout(2500)

    # --- Schritt 2: Jedes Profil öffnen (Spec, Sprache, Battletag) ---
    candidates = list(rows_by_key.values())
    print(f"\nPruefe {len(candidates)} Profile auf DPS und Deutsch ...")
    results = []
    for i, row in enumerate(candidates, start=1):
        label = f"  [{i}/{len(candidates)}] {row['character_name']}-{row['realm']}"
        try:
            page.goto(row["profile_url"], wait_until="domcontentloaded", timeout=45000)
            time.sleep(DELAY_PROFILE)
            row.update(parse_wowprogress_profile(page.inner_text("body")))
        except Exception as e:
            print(f"{label}: Fehler ({e})")
            continue

        # Sprache: Steht im Profil eine Sprache, muss German dabei sein.
        if row["languages"] and "german" not in row["languages"].lower():
            print(f"{label}: uebersprungen (Sprache: {row['languages']})")
            continue

        dps = is_dps(row)
        if dps is not True:
            grund = "kein DPS" if dps is False else "Rolle unklar"
            print(f"{label}: uebersprungen ({grund}: {row['specs'] or row['wow_class'] or '?'})")
            continue

        if CLASSES and row["wow_class"].lower() not in {c.lower() for c in CLASSES}:
            print(f"{label}: uebersprungen (Klasse {row['wow_class']})")
            continue

        print(f"{label}: OK ({row['wow_class']}, {row['specs'] or '-'})")
        results.append(row)

    print(f"\nWoWProgress: {len(results)} von {len(candidates)} passen.")
    return results


# ===========================================================================
# SPEICHERN
# ===========================================================================

RAIDERIO_FIELDS = ["character_name", "realm", "region", "wow_class", "guild", "ilvl",
                   "availability", "published", "discord", "twitch", "battletag",
                   "contact_raw", "profile_url"]

WOWPROGRESS_FIELDS = ["character_name", "realm", "region", "wow_class", "specs",
                      "guild", "ilvl", "languages", "raids_per_week", "published",
                      "battletag", "profile_url"]


def save_csv(rows: list[dict], path: Path, fields: list[str]):
    if not rows:
        print(f"\nKeine Daten zum Speichern fuer {path.name}.")
        return

    try:
        f = path.open("w", newline="", encoding="utf-8-sig")
    except PermissionError:
        # Passiert, wenn die Datei gerade in Excel offen ist.
        # Dann unter neuem Namen speichern, damit nichts verloren geht.
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        path = path.with_name(f"{path.stem}_{stamp}{path.suffix}")
        print(f"\nDatei ist gesperrt (in Excel offen?). Speichere stattdessen als {path.name}")
        f = path.open("w", newline="", encoding="utf-8-sig")

    with f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"\n{len(rows)} Profile gespeichert: {path}")


# ===========================================================================
# START
# ===========================================================================

def main():
    print(f"Rolle:   {ROLE} (fest)")
    print(f"Alter:   nur Gesuche juenger als {MAX_AGE_HOURS} Stunden")
    print(f"Klassen: {', '.join(CLASSES) if CLASSES else 'alle'}")
    print(f"Region:  {REGION} (fest)")
    print(f"Quellen: Raider.IO{' + WoWProgress' if RUN_WOWPROGRESS else ''}\n")

    with sync_playwright() as p:
        # Dauerhaftes Profil: Die Zustimmung wird zwischen den Läufen gemerkt.
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1600, "height": 1000},
        )
        page = context.pages[0] if context.pages else context.new_page()

        raiderio_rows = scrape_raiderio(page)
        # Gleich speichern, damit die Raider.IO-Liste sicher ist,
        # auch wenn bei WoWProgress etwas schiefgeht.
        save_csv(raiderio_rows, OUTPUT_CSV, RAIDERIO_FIELDS)

        if RUN_WOWPROGRESS:
            try:
                wowprogress_rows = scrape_wowprogress(page)
                save_csv(wowprogress_rows, WOWPROGRESS_CSV, WOWPROGRESS_FIELDS)
            except Exception as e:
                print(f"\nWoWProgress fehlgeschlagen: {e}")

        context.close()


if __name__ == "__main__":
    main()
