import re
import sys
import random
import calendar
import unicodedata
from dataclasses import dataclass
from datetime import datetime, date
from html.parser import HTMLParser
import html as htmlmod
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ------------------------------------------------------------------
# Version de l'application
# ------------------------------------------------------------------

__APP_NAME__ = "TideBuilder"
__VERSION__ = "0.1.0"


MONTHS_FR = {
    "janvier": 1,
    "février": 2,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
    "decembre": 12,
}

MONTHS_FR_CANON = {
    1: "janvier",
    2: "février",
    3: "mars",
    4: "avril",
    5: "mai",
    6: "juin",
    7: "juillet",
    8: "août",
    9: "septembre",
    10: "octobre",
    11: "novembre",
    12: "décembre",
}

# bibli de themes pour le selecteur
THEMES = {
    # ===== Thèmes sombres (sobres / quotidiens) =====
    "[Sombre] Midnight Garage": dict(
        BG="#151515", PANEL="#1F1F1F", FIELD="#2A2A2A",
        FG="#EAEAEA", FIELD_FG="#F0F0F0", ACCENT="#FF9800"
    ),
    "[Sombre] AIR-KLM Night flight": dict(
        BG="#0B1E2D", PANEL="#102A3D", FIELD="#16384F",
        FG="#EAF6FF", FIELD_FG="#FFFFFF", ACCENT="#00A1DE"
    ),
    "[Sombre] Café Serré": dict(
        BG="#1B120C", PANEL="#2A1C14", FIELD="#3A281D",
        FG="#F2E6D8", FIELD_FG="#FFF4E6", ACCENT="#C28E5C"
    ),
    "[Sombre] Matrix Déjà Vu": dict(
        BG="#000A00", PANEL="#001F00", FIELD="#003300",
        FG="#00FF66", FIELD_FG="#66FF99", ACCENT="#00FF00"
    ),
    "[Sombre] Miami Vice 1987": dict(
        BG="#14002E", PANEL="#2B0057", FIELD="#004D4D",
        FG="#FFF0FF", FIELD_FG="#FFFFFF", ACCENT="#00FFD5"
    ),
    "[Sombre] Cyber Licorne": dict(
        BG="#1A0026", PANEL="#2E004F", FIELD="#3D0066",
        FG="#F6E7FF", FIELD_FG="#FFFFFF", ACCENT="#FF2CF7"
    ),
    # ===== Thèmes clairs =====
    "[Clair] AIR-KLM Day flight": dict(
        BG="#EAF6FF", PANEL="#D6EEF9", FIELD="#FFFFFF",
        FG="#0B2A3F", FIELD_FG="#0B2A3F", ACCENT="#00A1DE"
    ),
    "[Clair] Matin Brumeux": dict(
        BG="#E6E7E8", PANEL="#D4D7DB", FIELD="#FFFFFF",
        FG="#1E1F22", FIELD_FG="#1E1F22", ACCENT="#6B7C93"
    ),
    "[Clair] Latte Vanille": dict(
        BG="#FAF6F1", PANEL="#EFE6DC", FIELD="#FFFFFF",
        FG="#3D2E22", FIELD_FG="#3D2E22", ACCENT="#D8B892"
    ),
    "[Clair] Miellerie La Divette": dict(
        BG="#E6B65C", PANEL="#F5E6CC", FIELD="#FFFFFF",
        FG="#50371A", FIELD_FG="#50371A", ACCENT="#F2B705"
    ),
    # ===== Thèmes Pouêt-Pouêt (mais distincts) =====
    "[Pouêt] Chewing-gum Océan": dict(
        BG="#00A6C8", PANEL="#0083A1", FIELD="#00C7B7",
        FG="#082026", FIELD_FG="#082026", ACCENT="#FF4FD8"
    ),
    "[Pouêt] Pamplemousse": dict(
        BG="#FF4A1C", PANEL="#E63B10", FIELD="#FF7A00",
        FG="#1A0B00", FIELD_FG="#1A0B00", ACCENT="#00E5FF"
    ),
    "[Pouêt] Raisin Toxique": dict(
        BG="#7A00FF", PANEL="#5B00C9", FIELD="#B000FF",
        FG="#0F001A", FIELD_FG="#0F001A", ACCENT="#39FF14"
    ),
    "[Pouêt] Citron qui pique": dict(
        BG="#FFF200", PANEL="#E6D800", FIELD="#FFF7A6",
        FG="#1A1A00", FIELD_FG="#1A1A00", ACCENT="#0066FF"
    ),
    "[Pouêt] Barbie Apocalypse": dict(
        BG="#FF1493", PANEL="#004D40", FIELD="#1B5E20",
        FG="#E8FFF8", FIELD_FG="#FFFFFF", ACCENT="#FFEB3B"
    ),
    "[Pouêt] Compagnie Créole": dict(
        BG="#8B3A1A", PANEL="#F2C94C", FIELD="#FFFFFF",
        FG="#5A2E0C", FIELD_FG="#5A2E0C", ACCENT="#8B3A1A"
    ),
}


@dataclass
class TideEvent:
    dt: datetime
    kind: str  # 'H' or 'L'
    height_m: float
    coef: int | None = None


def slugify(text: str) -> str:
    t = text.strip().lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", "_", t).strip("_")
    return t or "localite"


def parse_float_m(value: str) -> float:
    v = value.strip().lower().replace("m", "").replace(",", ".")
    return float(v)


def month_from_line(line: str) -> int | None:
    s = line.strip().lower()
    s = (
        s.replace("é", "e").replace("è", "e").replace("ê", "e")
        .replace("à", "a").replace("û", "u").replace("ô", "o")
        .replace("î", "i").replace("ï", "i").replace("ç", "c")
    )
    s = re.sub(r"\s+", " ", s)
    s = s.strip(" :\t")
    if s in MONTHS_FR:
        return MONTHS_FR[s]
    return None


def day_from_line(line: str) -> int | None:
    s = line.strip().lower()
    s = s.replace(".", " ")
    s = re.sub(r"\s+", " ", s)
    m = re.search(r"(\b[0-3]?\d)\s*$", s)
    if not m:
        return None
    d = int(m.group(1))
    if d < 1 or d > 31:
        return None
    return d


TIDE_RE = re.compile(
    r"mar[eé]e\s+(haute|basse)\s+(\d{1,2})h(\d{2})\s+([0-9]+(?:[.,][0-9]+)?)\s*m",
    re.IGNORECASE
)

COEF_RE = re.compile(r"^\s*(\d{2,3})\s*$")


def parse_paste_block(raw: str, year: int) -> tuple[list[TideEvent], list[str]]:
    warnings: list[str] = []
    events: list[TideEvent] = []

    current_month: int | None = None
    current_day: int | None = None
    last_high_without_coef: TideEvent | None = None

    lines = raw.splitlines()
    for idx, line in enumerate(lines, start=1):
        l = line.strip()
        if not l:
            continue

        mth = month_from_line(l)
        if mth is not None:
            current_month = mth
            current_day = None
            last_high_without_coef = None
            continue

        d = day_from_line(l)
        if d is not None:
            current_day = d
            last_high_without_coef = None
            continue

        m = TIDE_RE.search(l)
        if m:
            if current_month is None:
                warnings.append(f"Ligne {idx}: mois non détecté avant les marées.")
                continue
            if current_day is None:
                warnings.append(f"Ligne {idx}: jour non détecté avant les marées.")
                continue

            hb = m.group(1).lower()
            hh = int(m.group(2))
            mm = int(m.group(3))
            height = parse_float_m(m.group(4))

            kind = "H" if hb.startswith("hau") else "L"
            try:
                dt = datetime(year, current_month, current_day, hh, mm)
            except ValueError:
                warnings.append(
                    f"Ligne {idx}: date/heure invalide (mois={current_month}, jour={current_day}, {hh:02d}:{mm:02d})."
                )
                continue

            ev = TideEvent(dt=dt, kind=kind, height_m=height, coef=None)
            events.append(ev)

            if kind == "H":
                last_high_without_coef = ev
            else:
                last_high_without_coef = None
            continue

        c = COEF_RE.match(l)
        if c and last_high_without_coef is not None:
            last_high_without_coef.coef = int(c.group(1))
            last_high_without_coef = None
            continue

        continue

    events.sort(key=lambda e: e.dt)
    dedup: list[TideEvent] = []
    seen = set()
    for e in events:
        key = (e.dt, e.kind, round(e.height_m, 3), e.coef)
        if key in seen:
            continue
        seen.add(key)
        dedup.append(e)

    return dedup, warnings


class _TideHTMLParser(HTMLParser):
    def __init__(self, year: int, month: int):
        super().__init__()
        self.year = year
        self.month = month

        self.current_day: int | None = None

        self._in_tide_date_div = False
        self._in_tide_date_span = False

        self._in_high_tide = False
        self._in_low_tide = False

        self._capture_hour = False
        self._capture_height = False

        self._capture_coef_div = False
        self._capture_coef_span = False

        self._tmp_hour: str | None = None
        self._tmp_height: str | None = None

        self._line_events: list[TideEvent] = []
        self._line_coef: int | None = None

        self.events: list[TideEvent] = []
        self.warnings: list[str] = []

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        cls = attr.get("class", "")

        if tag == "div" and "tide-date" in cls:
            self._in_tide_date_div = True
            return

        if tag == "span" and self._in_tide_date_div:
            self._in_tide_date_span = True
            return

        if tag == "div" and "tide-line" in cls:
            self.commit_line()
            self._line_events = []
            self._line_coef = None
            return

        if tag == "div" and "high-tide" in cls:
            self._in_high_tide = True
            self._tmp_hour = None
            self._tmp_height = None
            return

        if tag == "div" and "low-tide" in cls:
            self._in_low_tide = True
            self._tmp_hour = None
            self._tmp_height = None
            return

        if tag == "span" and "hour" in cls and (self._in_high_tide or self._in_low_tide):
            self._capture_hour = True
            return

        if tag == "span" and "height" in cls and (self._in_high_tide or self._in_low_tide):
            self._capture_height = True
            return

        if tag == "div" and "coef" in cls:
            self._capture_coef_div = True
            return

        if tag == "span" and self._capture_coef_div:
            self._capture_coef_span = True
            return

    def handle_endtag(self, tag):
        if tag == "span":
            self._capture_hour = False
            self._capture_height = False
            self._capture_coef_span = False
            self._in_tide_date_span = False

        if tag == "div":
            if self._in_tide_date_div:
                self._in_tide_date_div = False

            if self._in_high_tide:
                self._finalize_tide(kind="H")
                self._in_high_tide = False

            if self._in_low_tide:
                self._finalize_tide(kind="L")
                self._in_low_tide = False

            if self._capture_coef_div:
                self._capture_coef_div = False

    def handle_data(self, data):
        txt = htmlmod.unescape(data).strip()
        if not txt:
            return

        if self._in_tide_date_span:
            m = re.search(r"(\b[0-3]?\d)\b", txt)
            if m:
                self.current_day = int(m.group(1))
            return

        if self._capture_hour:
            self._tmp_hour = txt
            return

        if self._capture_height:
            self._tmp_height = txt
            return

        if self._capture_coef_span:
            if re.fullmatch(r"\d{2,3}", txt):
                self._line_coef = int(txt)
            return

    def _finalize_tide(self, kind: str):
        if self.current_day is None:
            self.warnings.append("Jour non détecté avant une marée (HTML).")
            return
        if not self._tmp_hour or not self._tmp_height:
            return

        m = re.fullmatch(r"(\d{1,2})h(\d{2})", self._tmp_hour.strip())
        if not m:
            self.warnings.append(f"Heure invalide (HTML): {self._tmp_hour}")
            return

        hh = int(m.group(1))
        mm = int(m.group(2))

        try:
            height = parse_float_m(self._tmp_height)
        except Exception:
            self.warnings.append(f"Hauteur invalide (HTML): {self._tmp_height}")
            return

        try:
            dt = datetime(self.year, self.month, self.current_day, hh, mm)
        except ValueError:
            self.warnings.append(
                f"Date invalide (HTML): {self.year}-{self.month:02d}-{self.current_day:02d} {hh:02d}:{mm:02d}"
            )
            return

        ev = TideEvent(dt=dt, kind=kind, height_m=height, coef=None)
        self._line_events.append(ev)

        if kind == "H" and self._line_coef is not None:
            ev.coef = self._line_coef

    def commit_line(self):
        if not self._line_events:
            return

        if self._line_coef is not None:
            for e in self._line_events:
                if e.kind == "H":
                    e.coef = self._line_coef

        self.events.extend(self._line_events)
        self._line_events = []
        self._line_coef = None


def parse_html_block(raw_html: str, year: int) -> tuple[list[TideEvent], list[str]]:
    m = re.search(r'id="(\d{1,2})-(\d{1,2})"', raw_html)
    if not m:
        return [], ['Mois non détecté dans le HTML (ancre id="jj-mm" introuvable).']

    month = int(m.group(2))
    if month < 1 or month > 12:
        return [], [f"Mois invalide détecté dans le HTML : {month}"]

    inner = _TideHTMLParser(year=year, month=month)

    class _CommitWrapper(HTMLParser):
        def __init__(self, p: _TideHTMLParser):
            super().__init__()
            self.p = p

        def handle_starttag(self, tag, attrs):
            attr = dict(attrs)
            cls = attr.get("class", "")

            if tag == "div" and ("tide-date" in cls or "days-separator" in cls or "ephemeris" in cls):
                self.p.commit_line()

            self.p.handle_starttag(tag, attrs)

        def handle_endtag(self, tag):
            self.p.handle_endtag(tag)

        def handle_data(self, data):
            self.p.handle_data(data)

    w = _CommitWrapper(inner)
    w.feed(raw_html)
    inner.commit_line()

    evs = sorted(inner.events, key=lambda e: e.dt)
    dedup: list[TideEvent] = []
    seen = set()
    for e in evs:
        key = (e.dt, e.kind, round(e.height_m, 3), e.coef)
        if key in seen:
            continue
        seen.add(key)
        dedup.append(e)

    warnings = list(inner.warnings)
    return dedup, warnings


def build_output_text(locality: str, year: int, by_month: dict[int, list[TideEvent]]) -> str:
    all_events = [e for m in sorted(by_month) for e in by_month[m]]
    if all_events:
        all_events.sort(key=lambda e: e.dt)
        start = all_events[0].dt.date().isoformat()
        end = all_events[-1].dt.date().isoformat()
        extrait = f"(extrait: {start} -> {end})"
    else:
        extrait = "(extrait: vide)"

    header = (
        f"# Marees {locality} {year} {extrait}\n"
        f"# Format: YYYY-MM-DD;HH:MM;H|L;hauteur_m;coef\n"
    )

    out_lines = [header.rstrip("\n")]

    for m in range(1, 13):
        if m not in by_month or not by_month[m]:
            out_lines.append(f"# [MANQUANT] Mois: {MONTHS_FR_CANON[m]}")
            continue

        out_lines.append(f"# --- {MONTHS_FR_CANON[m]} ---")

        month_events = sorted(by_month[m], key=lambda e: e.dt)
        days_in_month = calendar.monthrange(year, m)[1]
        days_present = {e.dt.day for e in month_events}

        for d in range(1, days_in_month + 1):
            day_date = date(year, m, d)
            day_str = day_date.isoformat()

            if d not in days_present:
                out_lines.append(f"# [MANQUANT] Jour: {day_str}")
                continue

            for e in month_events:
                if e.dt.day != d:
                    continue
                ds = e.dt.strftime("%Y-%m-%d")
                ts = e.dt.strftime("%H:%M")
                kind = e.kind
                height = f"{e.height_m:.2f}".rstrip("0").rstrip(".")
                coef = str(e.coef) if (kind == "H" and e.coef is not None) else ""
                out_lines.append(f"{ds};{ts};{kind};{height};{coef}")

    return "\n".join(out_lines) + "\n"


def verify_dataset(year: int, by_month: dict[int, list[TideEvent]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    missing_months = [m for m in range(1, 13) if m not in by_month or not by_month[m]]
    if missing_months:
        warnings.append("Mois manquants : " + ", ".join(MONTHS_FR_CANON[m] for m in missing_months))

    for m, events in sorted(by_month.items()):
        if not events:
            continue

        days_in_month = calendar.monthrange(year, m)[1]
        days_present = {e.dt.day for e in events}
        missing_days = [d for d in range(1, days_in_month + 1) if d not in days_present]
        if missing_days:
            if len(missing_days) <= 10:
                warnings.append(f"{MONTHS_FR_CANON[m]} : jours manquants = {', '.join(str(d) for d in missing_days)}")
            else:
                warnings.append(
                    f"{MONTHS_FR_CANON[m]} : {len(missing_days)} jours manquants (ex: {', '.join(str(d) for d in missing_days[:10])} …)"
                )

        high_without_coef = [e for e in events if e.kind == "H" and e.coef is None]
        if high_without_coef:
            warnings.append(
                f"{MONTHS_FR_CANON[m]} : {len(high_without_coef)} marées hautes sans coefficient (souvent normal selon la source)."
            )

        # Trous temporels suspects (mois)
        month_events = sorted(events, key=lambda e: e.dt)
        GAP_WARN_S = int(9.5 * 3600)
        GAP_BIG_S = int(18.0 * 3600)

        for i in range(1, len(month_events)):
            prev = month_events[i - 1]
            cur = month_events[i]
            delta_s = int((cur.dt - prev.dt).total_seconds())

            if delta_s <= 0:
                errors.append(
                    f"{MONTHS_FR_CANON[m]} : ordre chronologique invalide entre "
                    f"{prev.dt.strftime('%Y-%m-%d %H:%M')} et {cur.dt.strftime('%Y-%m-%d %H:%M')}"
                )
                continue

            if delta_s > GAP_BIG_S:
                h = delta_s // 3600
                mi = (delta_s % 3600) // 60
                warnings.append(
                    f"{MONTHS_FR_CANON[m]} : trou énorme de {h}h{mi:02d} entre "
                    f"{prev.dt.strftime('%Y-%m-%d %H:%M')} et {cur.dt.strftime('%Y-%m-%d %H:%M')}"
                )
            elif delta_s > GAP_WARN_S:
                h = delta_s // 3600
                mi = (delta_s % 3600) // 60
                warnings.append(
                    f"{MONTHS_FR_CANON[m]} : trou suspect de {h}h{mi:02d} entre "
                    f"{prev.dt.strftime('%Y-%m-%d %H:%M')} et {cur.dt.strftime('%Y-%m-%d %H:%M')}"
                )

    all_events = [e for m in sorted(by_month) for e in by_month[m]]
    all_events.sort(key=lambda e: e.dt)
    seen_dt_kind = set()
    for e in all_events:
        k = (e.dt, e.kind)
        if k in seen_dt_kind:
            warnings.append(f"Doublon possible : {e.dt.strftime('%Y-%m-%d %H:%M')} {e.kind}")
        seen_dt_kind.add(k)

    if not all_events:
        errors.append("Aucun événement de marée n'a été importé.")

    return errors, warnings


class TideBuilderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Fabriqueur de fichiers marées (.txt HorlogeLune) — v{__VERSION__}")
        self.geometry("980x820")

        # --- Plateforme (tu avais ce bloc) ---
        self.is_mac = sys.platform == "darwin"
        self.is_linux = sys.platform.startswith("linux")
        self.is_windows = sys.platform.startswith("win")

        # --- Themes ---
        self._themes = THEMES
        self._theme_names = list(THEMES.keys())
        self._style = ttk.Style(self)

        # Essayer un thème ttk plus “colorable”
        try:
            if "clam" in self._style.theme_names():
                self._style.theme_use("clam")
        except Exception:
            pass

        # Thème aléatoire au démarrage
        self._theme_name = random.choice(self._theme_names)
        self._apply_theme_core(self._theme_name)

        self.by_month: dict[int, list[TideEvent]] = {}

        # --- Top controls ---
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Localité :").grid(row=0, column=0, sticky="w")
        self.var_locality = tk.StringVar(value="Cancale")
        self.entry_locality = ttk.Entry(top, textvariable=self.var_locality, width=30)
        self.entry_locality.grid(row=0, column=1, sticky="w", padx=(6, 18))

        ttk.Label(top, text="Année :").grid(row=0, column=2, sticky="w")
        self.var_year = tk.StringVar(value=str(date.today().year))
        self.entry_year = ttk.Entry(top, textvariable=self.var_year, width=8)
        self.entry_year.grid(row=0, column=3, sticky="w", padx=(6, 18))

        self.btn_import = ttk.Button(top, text="Importer", command=self.on_import)
        self.btn_import.grid(row=0, column=4, sticky="e")

        # Colonne "spacer"
        top.columnconfigure(5, weight=1)

        # --- Theme selector (en haut à droite) ---
        ttk.Label(top, text="Thème :").grid(row=0, column=6, sticky="e", padx=(0, 6))

        self.var_theme = tk.StringVar(value=self._theme_name)
        self.cbo_theme = ttk.Combobox(
            top,
            textvariable=self.var_theme,
            values=self._theme_names,
            state="readonly",
            width=28
        )
        self.cbo_theme.grid(row=0, column=7, sticky="e")
        self.cbo_theme.bind("<<ComboboxSelected>>", self.on_theme_changed)

        # --- Raw data block (5 lines) + buttons above it ---
        raw_frame = ttk.LabelFrame(self, text="Données marée (copier/coller brut)", padding=10)
        raw_frame.pack(fill="x", padx=10, pady=(0, 10))

        raw_btns = ttk.Frame(raw_frame)
        raw_btns.pack(fill="x", pady=(0, 6))

        self.btn_paste = ttk.Button(raw_btns, text="Coller", command=self.on_paste)
        self.btn_paste.pack(side="left")

        self.btn_clear_raw = ttk.Button(raw_btns, text="Tout effacer", command=self.on_clear_raw)
        self.btn_clear_raw.pack(side="left", padx=(10, 0))

        self.txt_raw = tk.Text(raw_frame, height=5, wrap="word")
        self.txt_raw.pack(fill="both", expand=False)

        # --- Output preview (30 lines) ---
        out_frame = ttk.LabelFrame(self, text="fichier.txt (aperçu construit)", padding=10)
        out_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.txt_out = tk.Text(out_frame, height=30, wrap="none")
        self.txt_out.pack(fill="both", expand=True)

        # --- Buttons bottom ---
        bottom = ttk.Frame(self, padding=10)
        bottom.pack(fill="x")

        self.btn_verify = ttk.Button(bottom, text="Vérifier", command=self.on_verify)
        self.btn_verify.pack(side="left")

        self.btn_save = ttk.Button(bottom, text="Enregistrer", command=self.on_save)
        self.btn_save.pack(side="left", padx=(10, 0))

        # Appliquer le thème aussi sur les Text (qui n’existaient pas au début)
        self.apply_theme(self._theme_name, update_combo=False)

        self.refresh_preview()

    # ---------------------- THEMING ----------------------

    def _apply_theme_core(self, theme_name: str):
        """
        Configure le style ttk + fond de fenêtre.
        (Les Text seront configurés dans apply_theme(), car ils peuvent ne pas exister encore.)
        """
        default_theme = next(iter(self._themes.values()))
        t = self._themes.get(theme_name, default_theme)

        bg = t["BG"]
        panel = t["PANEL"]
        field = t["FIELD"]
        fg = t["FG"]
        field_fg = t["FIELD_FG"]
        accent = t["ACCENT"]

        # Fond de la fenêtre principale
        try:
            self.configure(bg=bg)
        except Exception:
            pass

        # Styles ttk (clam supporte assez bien ces options)
        s = self._style
        s.configure(".", background=bg, foreground=fg)
        s.configure("TFrame", background=bg)
        s.configure("TLabelframe", background=bg, foreground=fg)
        s.configure("TLabelframe.Label", background=bg, foreground=fg)
        s.configure("TLabel", background=bg, foreground=fg)

        s.configure("TButton", background=panel, foreground=fg, padding=6)
        s.map(
            "TButton",
            background=[("active", accent)],
            foreground=[("active", field_fg)]
        )

        s.configure("TEntry", fieldbackground=field, foreground=field_fg)
        s.configure("TCombobox", fieldbackground=field, foreground=field_fg)

        try:
            s.map("TCombobox", fieldbackground=[("readonly", field)])
        except Exception:
            pass

        # Sélection (liste de la combobox)
        try:
            self.option_add("*TCombobox*Listbox.background", field)
            self.option_add("*TCombobox*Listbox.foreground", field_fg)
            self.option_add("*TCombobox*Listbox.selectBackground", accent)
            self.option_add("*TCombobox*Listbox.selectForeground", field_fg)
        except Exception:
            pass

    def apply_theme(self, theme_name: str, update_combo: bool = True):
        """
        Applique le thème ttk + configure aussi les widgets tk.Text.
        """
        self._theme_name = theme_name
        self._apply_theme_core(theme_name)

        default_theme = next(iter(self._themes.values()))
        t = self._themes.get(theme_name, default_theme)

        bg = t["BG"]
        panel = t["PANEL"]
        field = t["FIELD"]
        fg = t["FG"]
        field_fg = t["FIELD_FG"]
        accent = t["ACCENT"]

        # Text widgets
        for w in (getattr(self, "txt_raw", None), getattr(self, "txt_out", None)):
            if w is None:
                continue
            try:
                w.configure(
                    background=field,
                    foreground=field_fg,
                    insertbackground=field_fg,
                    selectbackground=accent,
                    selectforeground=field_fg,
                    highlightthickness=1,
                    highlightbackground=panel,
                    highlightcolor=accent,
                    relief="flat",
                    borderwidth=0
                )
            except Exception:
                pass

        # Mettre à jour la combobox sans relancer l’event
        if update_combo and hasattr(self, "var_theme"):
            try:
                self.var_theme.set(theme_name)
            except Exception:
                pass

    def on_theme_changed(self, _event=None):
        name = self.var_theme.get().strip()
        if name in self._themes:
            self.apply_theme(name, update_combo=False)

    # ---------------------- UI helpers ----------------------

    def on_paste(self):
        try:
            clip = self.clipboard_get()
        except Exception:
            messagebox.showwarning("Presse-papiers", "Le presse-papiers ne contient pas de texte.")
            return

        self.txt_raw.delete("1.0", "end")
        self.txt_raw.insert("1.0", clip)

    def on_clear_raw(self):
        self.txt_raw.delete("1.0", "end")

    # ---------------------- App logic ----------------------

    def get_year(self) -> int | None:
        try:
            y = int(self.var_year.get().strip())
            if y < 1900 or y > 2100:
                raise ValueError
            return y
        except Exception:
            messagebox.showerror("Année invalide", "Veuillez saisir une année valide (ex: 2026).")
            return None

    def refresh_preview(self):
        locality = self.var_locality.get().strip() or "Localité"
        try:
            y = int(self.var_year.get().strip())
        except Exception:
            y = date.today().year

        preview = build_output_text(locality, y, self.by_month)
        self.txt_out.delete("1.0", "end")
        self.txt_out.insert("1.0", preview)

    def on_import(self):
        y = self.get_year()
        if y is None:
            return

        raw = self.txt_raw.get("1.0", "end").strip()
        if not raw:
            messagebox.showwarning("Données vides", "Veuillez coller des données de marée avant d'importer.")
            return

        is_html = (
            "<div" in raw
            and ("high-tide" in raw or "low-tide" in raw)
            and ('class="hour"' in raw or "class='hour'" in raw)
        )

        if is_html:
            events, warnings = parse_html_block(raw, y)
        else:
            events, warnings = parse_paste_block(raw, y)

        if not events:
            msg = (
                "Aucune marée détectée dans le bloc collé.\n\n"
                "Conseil : vérifiez la présence de lignes du type :\n"
                "Marée haute 12h03 10.91m"
            )
            messagebox.showwarning("Import", msg)
            return

        for ev in events:
            m = ev.dt.month
            self.by_month.setdefault(m, [])
            self.by_month[m].append(ev)

        for m in list(self.by_month.keys()):
            month_events = sorted(self.by_month[m], key=lambda e: e.dt)
            dedup = []
            seen = set()
            for e in month_events:
                key = (e.dt, e.kind, round(e.height_m, 3), e.coef)
                if key in seen:
                    continue
                seen.add(key)
                dedup.append(e)
            self.by_month[m] = dedup

        self.refresh_preview()

        if warnings:
            head = "\n".join(warnings[:8])
            tail = "" if len(warnings) <= 8 else f"\n… (+{len(warnings) - 8} autres)"
            messagebox.showinfo("Import terminé", f"Marées importées : {len(events)}\n\nRemarques:\n{head}{tail}")
        else:
            messagebox.showinfo("Import terminé", f"Marées importées : {len(events)}")

    def on_verify(self):
        y = self.get_year()
        if y is None:
            return

        errors, warnings = verify_dataset(y, self.by_month)

        if errors:
            messagebox.showerror("Vérification", "Erreurs :\n- " + "\n- ".join(errors))
            return

        if warnings:
            messagebox.showwarning("Vérification", "Remarques :\n- " + "\n- ".join(warnings))
        else:
            messagebox.showinfo("Vérification", "Aucun problème détecté.")

    def on_save(self):
        y = self.get_year()
        if y is None:
            return

        locality = self.var_locality.get().strip()
        if not locality:
            messagebox.showwarning("Localité manquante", "Veuillez saisir une localité.")
            return

        errors, warnings = verify_dataset(y, self.by_month)
        if errors:
            messagebox.showerror("Enregistrement", "Impossible d'enregistrer :\n- " + "\n- ".join(errors))
            return

        yy = str(y)[-2:]
        default_name = f"MAREE{yy}_{slugify(locality)}.txt"

        path = filedialog.asksaveasfilename(
            title="Enregistrer le fichier de marées",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        if not path:
            return

        txt = build_output_text(locality, y, self.by_month)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(txt)
        except Exception as e:
            messagebox.showerror("Enregistrement", f"Erreur d'écriture : {e}")
            return

        if warnings:
            messagebox.showinfo("Enregistrement", f"Fichier enregistré.\n\nRemarques:\n- " + "\n- ".join(warnings))
        else:
            messagebox.showinfo("Enregistrement", "Fichier enregistré.")


if __name__ == "__main__":
    app = TideBuilderApp()
    app.mainloop()