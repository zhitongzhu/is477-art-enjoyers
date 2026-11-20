"""
Preliminary artist-level integration and record linkage.

Links artists across:
  * The Met (data/raw/met_artworks.csv)
  * Cleveland Museum of Art (data/raw/cleveland_artworks.json)
  * Wikidata SPARQL bindings (data/raw/wikidata_artists.json)

STATUS: PRELIMINARY. This version runs on the *raw* files for the interim
report. The final version should be pointed at Bernice's cleaned files via
the --met / --cleveland / --wikidata arguments (see docs/integration_plan.md).
Raw files are only read, never modified.

Usage (from the repository root):
    python scripts/integrate.py
    python scripts/integrate.py --sample-cleveland 500 --seed 477

Outputs:
    results/preliminary/*.csv, *.json, *.md   (small, committed)
    data/integrated/artwork_artist_integrated.csv  (large, git-ignored)
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MET_COLUMNS = [
    "Object ID",
    "Constituent ID",
    "Artist Role",
    "Artist Display Name",
    "Artist Nationality",
    "Artist Begin Date",
    "Artist End Date",
    "Artist Wikidata URL",
    "Object Begin Date",
    "Object End Date",
]

# Met packs several creators into one cell, separated by "|".
MET_MULTI_COLUMNS = [
    "Artist Role",
    "Artist Display Name",
    "Artist Nationality",
    "Artist Begin Date",
    "Artist End Date",
    "Artist Wikidata URL",
]

# Names that do not identify a single person and must never be matched.
ANONYMOUS_PATTERN = re.compile(
    r"^(anonymous|unknown|unidentified|artist unknown|various artists?)\b",
    re.IGNORECASE,
)

QID_PATTERN = re.compile(r"Q[1-9]\d*")
YEAR_PATTERN = re.compile(r"^-?\d{1,4}$")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def normalize_name(name: str | None) -> str:
    """Lower-case, strip accents and punctuation, collapse whitespace.

    'Narcisse Díaz de la Peña' -> 'narcisse diaz de la pena'
    Non-Latin characters (e.g. Japanese) are kept as-is.
    """
    if not name:
        return ""
    text = unicodedata.normalize("NFKD", str(name))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^\w\s]", " ", text)   # punctuation -> space
    text = re.sub(r"_", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def name_variants(name: str | None) -> set[str]:
    """All normalized forms of a name we are willing to match on.

    Adds a Latin-only form so that 'Kano Motonobu 狩野元信' also matches
    'Kano Motonobu', and the text inside / outside parentheses so that
    'Rembrandt (Rembrandt van Rijn)' yields both.
    """
    if not name:
        return set()
    raw = str(name)
    pieces = {raw}
    paren = re.match(r"^(.*?)\s*\((.*)\)\s*$", raw)
    if paren:
        pieces.update({paren.group(1), paren.group(2)})
    out = set()
    for piece in pieces:
        norm = normalize_name(piece)
        if norm:
            out.add(norm)
        latin = " ".join(t for t in norm.split() if t.isascii())
        if latin:
            out.add(latin)
    # Single-token variants are too weak (e.g. 'bronzino', 'and').
    return {v for v in out if len(v.split()) >= 2 or v == normalize_name(raw)}


def parse_year(value) -> int | None:
    """'1859      ' -> 1859, '-0500' -> -500, '' / None -> None."""
    if value is None:
        return None
    text = str(value).strip()
    if not YEAR_PATTERN.match(text):
        return None
    return int(text)


def wikidata_year(value: str | None) -> int | None:
    """'1856-01-01T00:00:00Z' -> 1856, '-0600-...' -> -600.

    Wikidata 'unknown value' blank nodes (…/.well-known/genid/…) -> None.
    """
    if not value or "genid" in value:
        return None
    match = re.match(r"^(-?)(\d{1,4})-", value)
    if not match:
        return None
    year = int(match.group(2))
    return -year if match.group(1) else year


def is_anonymous(name: str | None) -> bool:
    return not name or bool(ANONYMOUS_PATTERN.match(str(name).strip()))


def years_agree(a: int | None, b: int | None, tol: int) -> bool | None:
    """True/False if both known, None if either side is missing."""
    if a is None or b is None or pd.isna(a) or pd.isna(b):  # NaN != None!
        return None
    return abs(a - b) <= tol


def join_unique(values) -> str:
    seen = sorted({str(v) for v in values if v not in (None, "") and not pd.isna(v)})
    return "; ".join(seen)


# ---------------------------------------------------------------------------
# 1. The Met
# ---------------------------------------------------------------------------

def load_met(path: Path) -> pd.DataFrame:
    """Return one row per (artwork, creator position)."""
    met = pd.read_csv(
        path,
        usecols=MET_COLUMNS,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",  # file starts with a BOM
    )[MET_COLUMNS]  # usecols keeps file order; force ours

    rows = []
    misaligned = 0
    for rec in met.itertuples(index=False, name=None):
        values = dict(zip(MET_COLUMNS, rec))
        if not values["Artist Display Name"].strip():
            continue  # artwork with no named creator

        split = {c: values[c].split("|") for c in MET_MULTI_COLUMNS}
        lengths = {len(v) for v in split.values()}
        n = len(split["Artist Display Name"])
        if len(lengths) != 1:
            # Positions cannot be trusted; keep names only.
            misaligned += 1

        for i in range(n):
            def get(col):
                parts = split[col]
                return parts[i].strip() if len(lengths) == 1 and i < len(parts) else ""

            name = split["Artist Display Name"][i].strip()
            qids = QID_PATTERN.findall(get("Artist Wikidata URL"))
            rows.append({
                "museum": "met",
                "artwork_id": values["Object ID"],
                "position": i,
                "n_creators_on_artwork": n,
                "role": get("Artist Role"),
                "qualifier": "",
                "artist_name": name,
                "nationality_museum": get("Artist Nationality"),
                "birth_year_museum": parse_year(get("Artist Begin Date")),
                # Met uses 9999 for 'still active / living'
                "death_year_museum": (lambda y: None if y == 9999 else y)(
                    parse_year(get("Artist End Date"))
                ),
                "qid": qids[0] if qids else "",
                "n_qids_in_cell": len(qids),
                "object_begin_date": parse_year(values["Object Begin Date"]),
                "object_end_date": parse_year(values["Object End Date"]),
                "met_constituent_id_raw": values["Constituent ID"],
            })

    links = pd.DataFrame(rows)
    links["is_anonymous"] = links["artist_name"].map(is_anonymous)
    links["name_norm"] = links["artist_name"].map(normalize_name)
    links.attrs["misaligned_rows"] = misaligned
    links.attrs["artwork_rows"] = len(met)
    return links


def assign_met_artist_keys(links: pd.DataFrame) -> pd.DataFrame:
    """Give every Met creator mention a local artist key.

    We do NOT use 'Constituent ID': in this CSV it is concatenated without a
    delimiter for multi-creator artworks and is reused across different
    names (see results/preliminary/match_summary.md).

      * with a Wikidata QID      -> 'wd:Q…'
      * without, named           -> 'met:<normalized name>|<birth>|<death>'
      * anonymous / unknown      -> ''  (never matched)
    """
    def key(row):
        if row["is_anonymous"]:
            return ""
        if row["qid"]:
            return f"wd:{row['qid']}"
        b = "" if pd.isna(row["birth_year_museum"]) else int(row["birth_year_museum"])
        d = "" if pd.isna(row["death_year_museum"]) else int(row["death_year_museum"])
        return f"met:{row['name_norm']}|{b}|{d}"

    links = links.copy()
    links["met_artist_key"] = links.apply(key, axis=1)
    return links


def build_met_artists(links: pd.DataFrame) -> pd.DataFrame:
    named = links[links["met_artist_key"] != ""]

    def mode(series):
        s = series.dropna()
        s = s[s.astype(str) != ""]
        return s.mode().iloc[0] if not s.empty else None

    grouped = named.groupby("met_artist_key")
    artists = pd.DataFrame({
        "artist_name": grouped["artist_name"].agg(mode),
        "name_variants": grouped["artist_name"].agg(join_unique),
        "qid": grouped["qid"].agg(lambda s: mode(s) or ""),
        "nationality_met": grouped["nationality_museum"].agg(join_unique),
        "birth_year_met": grouped["birth_year_museum"].agg(mode),
        "death_year_met": grouped["death_year_museum"].agg(mode),
        "n_distinct_birth_years_met": grouped["birth_year_museum"].nunique(),
        "met_artwork_count": grouped["artwork_id"].nunique(),  # distinct artworks
    }).reset_index()
    return artists


# ---------------------------------------------------------------------------
# 2. Wikidata
# ---------------------------------------------------------------------------

def load_wikidata(path: Path) -> pd.DataFrame:
    """Collapse SPARQL bindings (one row per artist x date x country) to one
    row per QID. Multiple citizenships stay in ONE row as a '; ' list so they
    can never multiply artwork counts in a join."""
    with open(path, encoding="utf-8") as f:
        bindings = json.load(f)

    acc: dict[str, dict] = {}
    for b in bindings:
        qid = b["artist"]["value"].rsplit("/", 1)[-1]
        a = acc.setdefault(qid, {"labels": set(), "births": set(),
                                 "deaths": set(), "countries": set()})
        label = b.get("artistLabel", {}).get("value", "")
        if label and label != qid:          # label == QID means no English label
            a["labels"].add(label)
        if "birthDate" in b:
            a["births"].add(wikidata_year(b["birthDate"]["value"]))
        if "deathDate" in b:
            a["deaths"].add(wikidata_year(b["deathDate"]["value"]))
        if "countryLabel" in b:
            a["countries"].add(b["countryLabel"]["value"])

    rows = []
    for qid, a in acc.items():
        births = sorted(y for y in a["births"] if y is not None)
        deaths = sorted(y for y in a["deaths"] if y is not None)
        rows.append({
            "qid": qid,
            "wd_label": sorted(a["labels"])[0] if a["labels"] else "",
            # A single value only when Wikidata is unambiguous.
            "birth_year_wd": births[0] if len(births) == 1 else None,
            "death_year_wd": deaths[0] if len(deaths) == 1 else None,
            "wd_birth_years_all": "; ".join(map(str, births)),
            "wd_death_years_all": "; ".join(map(str, deaths)),
            "wd_countries": "; ".join(sorted(a["countries"])),
            "wd_n_countries": len(a["countries"]),
        })
    wd = pd.DataFrame(rows)
    wd.attrs["bindings"] = len(bindings)
    return wd


# ---------------------------------------------------------------------------
# 3. Cleveland
# ---------------------------------------------------------------------------

def parse_cleveland_description(desc: str | None) -> tuple[str, str, int | None, int | None]:
    """'Camille Pissarro (French, 1830–1903)' -> ('Camille Pissarro', 'French', 1830, 1903)."""
    if not desc:
        return "", "", None, None
    m = re.match(r"^(.*?)\s*\((.*)\)\s*$", desc)
    if not m:
        return desc.strip(), "", None, None
    name, inner = m.group(1).strip(), m.group(2)
    first = inner.split(",")[0].strip()
    nationality = "" if re.search(r"\d", first) else first
    years = [int(y) for y in re.findall(r"(?<!\d)(\d{3,4})(?!\d)", inner)]
    birth = death = None
    if re.search(r"\b(b\.|born)\s*\d", inner):
        birth = years[0] if years else None
    elif years:
        birth = years[0]
        death = years[1] if len(years) > 1 else None
    return name, nationality, birth, death


def load_cleveland(path: Path) -> pd.DataFrame:
    """Return one row per (artwork, creator)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    artworks = data.get("data", []) if isinstance(data, dict) else data

    rows = []
    for art in artworks:
        creators = art.get("creators") or []
        for pos, c in enumerate(creators):
            name, nat, d_birth, d_death = parse_cleveland_description(c.get("description"))
            rows.append({
                "museum": "cleveland",
                "artwork_id": str(art["id"]),
                "position": pos,
                "n_creators_on_artwork": len(creators),
                "role": c.get("role") or "",
                "qualifier": c.get("qualifier") or "",
                "artist_name": name,
                "cle_description": c.get("description") or "",
                "nationality_museum": nat,
                "birth_year_museum": parse_year(c.get("birth_year")),
                "death_year_museum": parse_year(c.get("death_year")),
                "desc_birth_year": d_birth,
                "desc_death_year": d_death,
                "cle_creator_id": str(c["id"]),
                "object_begin_date": art.get("creation_date_earliest"),
                "object_end_date": art.get("creation_date_latest"),
            })
    links = pd.DataFrame(rows)
    links["is_anonymous"] = links["artist_name"].map(is_anonymous)
    links["name_norm"] = links["artist_name"].map(normalize_name)
    links.attrs["artworks"] = len(artworks)
    links.attrs["artworks_with_creators"] = sum(bool(a.get("creators")) for a in artworks)
    return links


def build_cleveland_artists(links: pd.DataFrame) -> pd.DataFrame:
    g = links.groupby("cle_creator_id")

    def first_nonnull(s):
        s = s.dropna()
        return s.iloc[0] if not s.empty else None

    artists = pd.DataFrame({
        "artist_name": g["artist_name"].agg(lambda s: s.mode().iloc[0]),
        "descriptions": g["cle_description"].agg(join_unique),
        "nationality_cle": g["nationality_museum"].agg(join_unique),
        "birth_year_cle": g["birth_year_museum"].agg(first_nonnull),
        "death_year_cle": g["death_year_museum"].agg(first_nonnull),
        "desc_birth_year": g["desc_birth_year"].agg(first_nonnull),
        "desc_death_year": g["desc_death_year"].agg(first_nonnull),
        "is_anonymous": g["is_anonymous"].agg("all"),
        "cle_artwork_count": g["artwork_id"].nunique(),
        "cle_artwork_count_unqualified": g.apply(
            lambda d: d.loc[d["qualifier"] == "", "artwork_id"].nunique(),
            include_groups=False,
        ),
    }).reset_index()

    # Structured years vs years written in the description text
    def conflict(row):
        out = []
        for a, b, label in [("birth_year_cle", "desc_birth_year", "birth"),
                            ("death_year_cle", "desc_death_year", "death")]:
            if pd.notna(row[a]) and pd.notna(row[b]) and abs(row[a] - row[b]) > 1:
                out.append(f"{label}: field={int(row[a])} text={int(row[b])}")
        return "; ".join(out)

    artists["internal_date_conflict"] = artists.apply(conflict, axis=1)
    return artists


# ---------------------------------------------------------------------------
# 4. Linkage
# ---------------------------------------------------------------------------

def link_met_to_wikidata(met_artists: pd.DataFrame, wd: pd.DataFrame, tol: int) -> pd.DataFrame:
    """Met artists that carry a QID: identifier link, then a date sanity check."""
    with_qid = met_artists[met_artists["qid"] != ""]
    merged = with_qid.merge(wd, on="qid", how="left", validate="many_to_one",
                            indicator=True)

    def status(row):
        if row["_merge"] == "left_only":
            # acquire_wikidata.py keeps only humans (P31=Q5): firms drop out.
            return "qid_not_in_wikidata_file"
        b = years_agree(row["birth_year_met"], row["birth_year_wd"], tol)
        d = years_agree(row["death_year_met"], row["death_year_wd"], tol)
        if b is False or d is False:
            return "confirmed_qid_date_conflict"
        return "confirmed_qid"

    merged["link_status"] = merged.apply(status, axis=1)
    return merged.drop(columns="_merge")


def build_candidate_entities(met_artists: pd.DataFrame, wd: pd.DataFrame) -> pd.DataFrame:
    """One row per matchable entity, keyed by QID where we have one.

    Several Met keys can share a QID (spelling variants); they collapse here.
    Wikidata labels add extra name variants for those QIDs.
    """
    wd_idx = wd.set_index("qid")
    rows = []
    for qid, grp in met_artists[met_artists["qid"] != ""].groupby("qid"):
        names = set()
        for v in grp["name_variants"]:
            names.update(v.split("; "))
        w = wd_idx.loc[qid] if qid in wd_idx.index else None
        if w is not None and w["wd_label"]:
            names.add(w["wd_label"])
        rows.append({
            "entity_id": f"wd:{qid}", "qid": qid, "names": names,
            "birth_met": grp["birth_year_met"].dropna().astype(int).tolist(),
            "death_met": grp["death_year_met"].dropna().astype(int).tolist(),
            "birth_wd": None if w is None else w["birth_year_wd"],
            "death_wd": None if w is None else w["death_year_wd"],
            "met_artwork_count": int(grp["met_artwork_count"].sum()),
        })
    for rec in met_artists[met_artists["qid"] == ""].itertuples():
        rows.append({
            "entity_id": rec.met_artist_key, "qid": "",
            "names": set(rec.name_variants.split("; ")),
            "birth_met": [] if pd.isna(rec.birth_year_met) else [int(rec.birth_year_met)],
            "death_met": [] if pd.isna(rec.death_year_met) else [int(rec.death_year_met)],
            "birth_wd": None, "death_wd": None,
            "met_artwork_count": int(rec.met_artwork_count),
        })
    return pd.DataFrame(rows)


def evaluate(years_cle: int | None, years_cand: list[int], tol: int) -> bool | None:
    if years_cle is None or pd.isna(years_cle) or not years_cand:
        return None
    return any(abs(int(years_cle) - y) <= tol for y in years_cand)


def match_cleveland(cle_artists: pd.DataFrame, entities: pd.DataFrame, tol: int):
    """Match Cleveland creators to Met/Wikidata entities.

    Blocking: exact equality of a normalized name variant.
    Evidence: birth year and death year (± tol years).

    Per candidate:
      strong     name + birth agree, and death agrees (or both sides lack death)
      conflict   name matches but a known year disagrees beyond tolerance
      weak       name matches, not enough dates to decide

    Per Cleveland creator:
      confirmed  exactly one strong candidate
      ambiguous  >1 strong, or only weak/conflict candidates -> manual review
      unmatched  no candidate shares a name
      excluded   anonymous / unknown creator
    """
    index: dict[str, set[int]] = {}
    for i, names in enumerate(entities["names"]):
        for n in names:
            for v in name_variants(n):
                index.setdefault(v, set()).add(i)

    cand_rows, result_rows = [], []
    for cle in cle_artists.itertuples(index=False):
        base = {"cle_creator_id": cle.cle_creator_id, "cle_name": cle.artist_name,
                "cle_birth": cle.birth_year_cle, "cle_death": cle.death_year_cle}
        if cle.is_anonymous:
            result_rows.append({**base, "match_status": "excluded_anonymous",
                                "reason": "anonymous/unknown creator",
                                "matched_entity_id": "", "matched_qid": "",
                                "n_name_candidates": 0})
            continue

        hits = set()
        for v in name_variants(cle.artist_name):
            hits |= index.get(v, set())

        strong, weak, conflict = [], [], []
        for i in hits:
            e = entities.iloc[i]
            births = e["birth_met"] + ([int(e["birth_wd"])] if pd.notna(e["birth_wd"]) else [])
            deaths = e["death_met"] + ([int(e["death_wd"])] if pd.notna(e["death_wd"]) else [])
            b = evaluate(cle.birth_year_cle, births, tol)
            d = evaluate(cle.death_year_cle, deaths, tol)
            both_living = pd.isna(cle.death_year_cle) and not deaths
            if b is False or d is False:
                verdict = "conflict"
                conflict.append(i)
            elif b is True and (d is True or both_living):
                verdict = "strong"
                strong.append(i)
            else:
                verdict = "weak"
                weak.append(i)
            cand_rows.append({**base, "entity_id": e["entity_id"], "qid": e["qid"],
                              "cand_births": "; ".join(map(str, sorted(set(births)))),
                              "cand_deaths": "; ".join(map(str, sorted(set(deaths)))),
                              "birth_agree": b, "death_agree": d, "verdict": verdict})

        if not hits:
            status, reason, chosen = "unmatched", "no Met/Wikidata name match", None
        elif len(strong) == 1:
            status, chosen = "confirmed", strong[0]
            reason = "name + birth/death years agree"
            if weak or conflict:
                reason += f" ({len(weak) + len(conflict)} other same-name candidate(s) rejected/weak)"
        elif len(strong) > 1:
            # Usually the Met holds duplicate records for one person (e.g. a
            # QID record plus a no-QID spelling variant). If the strong
            # candidates point to at most ONE QID, they are the same person:
            # pick the QID record (else the one with most artworks).
            qids = {entities.iloc[i]["qid"] for i in strong} - {""}
            if len(qids) <= 1:
                chosen = max(strong, key=lambda i: (entities.iloc[i]["qid"] != "",
                                                    entities.iloc[i]["met_artwork_count"]))
                status = "confirmed"
                reason = (f"name + birth/death years agree; {len(strong)} Met records "
                          "for the same person (Met-side duplicates)")
            else:
                status, reason, chosen = ("ambiguous",
                                          "same name + dates but different Wikidata QIDs", None)
        elif conflict and not weak:
            status, reason, chosen = ("ambiguous", "same name but a year disagrees beyond "
                                      "tolerance (data error or different person)", None)
        else:
            status, reason, chosen = "ambiguous", "same name, insufficient dates to confirm", None

        e = entities.iloc[chosen] if chosen is not None else None
        result_rows.append({**base, "match_status": status, "reason": reason,
                            "matched_entity_id": "" if e is None else e["entity_id"],
                            "matched_qid": "" if e is None else e["qid"],
                            "n_name_candidates": len(hits)})

    return pd.DataFrame(result_rows), pd.DataFrame(cand_rows)


# ---------------------------------------------------------------------------
# 5. Integrated artwork-artist table
# ---------------------------------------------------------------------------

def build_integrated(met_links, cle_links, cle_matches, wd) -> pd.DataFrame:
    """One row per (museum, artwork, creator). Joins are many-to-one only, and
    the row count is asserted unchanged, so artwork counts cannot inflate."""
    met = met_links.assign(
        local_artist_id=met_links["met_artist_key"],
        unified_artist_id=met_links["met_artist_key"],
        match_status=met_links["qid"].map(lambda q: "met_qid" if q else "met_no_qid"),
    )
    met.loc[met["is_anonymous"], "match_status"] = "excluded_anonymous"

    m = cle_matches.set_index("cle_creator_id")
    cle = cle_links.assign(local_artist_id="cle:" + cle_links["cle_creator_id"])
    cle["match_status"] = cle["cle_creator_id"].map(m["match_status"])
    matched = cle["cle_creator_id"].map(m["matched_entity_id"]).fillna("")
    cle["qid"] = cle["cle_creator_id"].map(m["matched_qid"]).fillna("")
    cle["unified_artist_id"] = matched.where(matched != "", cle["local_artist_id"])

    keep = ["museum", "artwork_id", "position", "n_creators_on_artwork", "role",
            "qualifier", "artist_name", "local_artist_id", "unified_artist_id",
            "match_status", "qid", "nationality_museum", "birth_year_museum",
            "death_year_museum", "object_begin_date", "object_end_date"]
    both = pd.concat([met[keep], cle[keep]], ignore_index=True)
    n_before = len(both)

    both = both.merge(
        wd[["qid", "wd_label", "birth_year_wd", "death_year_wd", "wd_countries"]],
        on="qid", how="left", validate="many_to_one",
    )
    assert len(both) == n_before, "join changed row count"

    # Enriched columns: museum value first, Wikidata fills the gaps.
    both["birth_year"] = both["birth_year_museum"].fillna(both["birth_year_wd"])
    both["death_year"] = both["death_year_museum"].fillna(both["death_year_wd"])
    return both


# ---------------------------------------------------------------------------
# 6. Driver
# ---------------------------------------------------------------------------

def pct(a, b):
    return round(100 * a / b, 1) if b else 0.0


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--met", default="data/raw/met_artworks.csv")
    p.add_argument("--cleveland", default="data/raw/cleveland_artworks.json")
    p.add_argument("--wikidata", default="data/raw/wikidata_artists.json")
    p.add_argument("--out", default="results/preliminary")
    p.add_argument("--integrated-out", default="data/integrated")
    p.add_argument("--year-tolerance", type=int, default=2,
                   help="max difference in years still counted as agreeing")
    p.add_argument("--sample-cleveland", type=int, default=0,
                   help="match only N randomly chosen Cleveland creators (0 = all)")
    p.add_argument("--seed", type=int, default=477)
    args = p.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tol = args.year_tolerance

    print("Loading Met …")
    met_links = assign_met_artist_keys(load_met(Path(args.met)))
    met_artists = build_met_artists(met_links)

    print("Loading Wikidata …")
    wd = load_wikidata(Path(args.wikidata))

    print("Loading Cleveland …")
    cle_links = load_cleveland(Path(args.cleveland))
    cle_artists = build_cleveland_artists(cle_links)

    print("Linking Met -> Wikidata …")
    met_wd = link_met_to_wikidata(met_artists, wd, tol)

    print("Matching Cleveland -> Met/Wikidata …")
    entities = build_candidate_entities(met_artists, wd)
    to_match = cle_artists
    if args.sample_cleveland:
        to_match = cle_artists.sample(n=min(args.sample_cleveland, len(cle_artists)),
                                      random_state=args.seed)
    cle_matches, cle_candidates = match_cleveland(to_match, entities, tol)

    # ---- write artist-level results (small) ----
    met_artists.to_csv(out / "met_artists.csv", index=False)
    met_wd.to_csv(out / "met_wikidata_links.csv", index=False)
    cle_artists.to_csv(out / "cleveland_artists.csv", index=False)
    cle_matches.to_csv(out / "cleveland_matches.csv", index=False)
    cle_candidates.to_csv(out / "cleveland_match_candidates.csv", index=False)
    for status in ["confirmed", "ambiguous", "unmatched"]:
        cle_matches[cle_matches["match_status"] == status].to_csv(
            out / f"cleveland_{status}.csv", index=False)

    # Several Cleveland creator IDs confirmed to the same person -> likely
    # duplicate creator records in Cleveland (flag for cleaning).
    conf = cle_matches[cle_matches["match_status"] == "confirmed"]
    cle_dups = conf[conf.duplicated("matched_entity_id", keep=False)].sort_values(
        "matched_entity_id")
    cle_dups.to_csv(out / "cleveland_possible_duplicate_creators.csv", index=False)

    # Fixed random sample for manual review (documented in docs/).
    review = pd.concat([
        conf.sample(n=min(25, len(conf)), random_state=args.seed),
        cle_matches[cle_matches["match_status"] == "ambiguous"].sample(
            n=min(25, (cle_matches["match_status"] == "ambiguous").sum()),
            random_state=args.seed),
    ])
    review.assign(reviewer_verdict="", reviewer_note="").to_csv(
        out / "manual_review_sample.csv", index=False)

    # ---- integrated artwork-artist table (large, git-ignored) ----
    integrated = None
    if not args.sample_cleveland:
        integrated = build_integrated(met_links, cle_links, cle_matches, wd)
        int_dir = Path(args.integrated_out)
        int_dir.mkdir(parents=True, exist_ok=True)
        integrated.to_csv(int_dir / "artwork_artist_integrated.csv", index=False)
        integrated.sample(n=2000, random_state=args.seed).sort_values(
            ["museum", "artwork_id", "position"]).to_csv(
            out / "integrated_sample_2000.csv", index=False)

    # ---- summary numbers ----
    status_counts = cle_matches["match_status"].value_counts().to_dict()
    reason_counts = cle_matches.groupby(["match_status", "reason"]).size()
    named_met = met_links[met_links["met_artist_key"] != ""]

    s = {
        "inputs": {"met": args.met, "cleveland": args.cleveland, "wikidata": args.wikidata,
                   "note": "PRELIMINARY run on raw (uncleaned) data"},
        "parameters": {"year_tolerance": tol, "sample_cleveland": args.sample_cleveland,
                       "seed": args.seed},
        "met": {
            "artwork_rows": met_links.attrs["artwork_rows"],
            "artworks_with_named_creator": int(met_links["artwork_id"].nunique()),
            "creator_mentions": len(met_links),
            "anonymous_mentions": int(met_links["is_anonymous"].sum()),
            "misaligned_multi_value_rows": met_links.attrs["misaligned_rows"],
            "mentions_with_qid": int((named_met["qid"] != "").sum()),
            "distinct_artist_keys": len(met_artists),
            "distinct_qids": int((met_artists["qid"] != "").sum()),
            "artist_keys_without_qid": int((met_artists["qid"] == "").sum()),
            "cells_with_more_than_one_qid_for_one_creator": int((met_links["n_qids_in_cell"] > 1).sum()),
        },
        "wikidata": {
            "bindings": wd.attrs["bindings"],
            "distinct_qids": len(wd),
            "multiple_birth_years": int(wd["wd_birth_years_all"].str.contains(";").sum()),
            "multiple_death_years": int(wd["wd_death_years_all"].str.contains(";").sum()),
            "multiple_countries": int((wd["wd_n_countries"] > 1).sum()),
            "no_english_label": int((wd["wd_label"] == "").sum()),
        },
        "met_to_wikidata": met_wd["link_status"].value_counts().to_dict(),
        "cleveland": {
            "artworks": cle_links.attrs["artworks"],
            "artworks_with_creators": cle_links.attrs["artworks_with_creators"],
            "creator_mentions": len(cle_links),
            "distinct_creators": len(cle_artists),
            "anonymous_creators": int(cle_artists["is_anonymous"].sum()),
            "creators_with_internal_date_conflict": int((cle_artists["internal_date_conflict"] != "").sum()),
            "creators_matched_in_this_run": len(cle_matches),
            "creator_ids_confirmed_to_an_entity_shared_with_another_id": len(cle_dups),
        },
        "cleveland_match_status": status_counts,
        "cleveland_match_reasons": {f"{k[0]} | {k[1]}": int(v) for k, v in reason_counts.items()},
    }

    if integrated is not None:
        comp = {}
        for museum, grp in integrated[integrated["match_status"] != "excluded_anonymous"].groupby("museum"):
            artists = grp.drop_duplicates("unified_artist_id")
            n = len(artists)
            comp[museum] = {
                "distinct_artists": n,
                "birth_year_known_museum_pct": pct(artists["birth_year_museum"].notna().sum(), n),
                "birth_year_known_after_wikidata_pct": pct(artists["birth_year"].notna().sum(), n),
                "death_year_known_museum_pct": pct(artists["death_year_museum"].notna().sum(), n),
                "death_year_known_after_wikidata_pct": pct(artists["death_year"].notna().sum(), n),
                "nationality_known_museum_pct": pct((artists["nationality_museum"] != "").sum(), n),
                "citizenship_known_wikidata_pct": pct(artists["wd_countries"].fillna("").ne("").sum(), n),
            }
        overlap = cle_matches[cle_matches["match_status"] == "confirmed"]
        s["completeness_by_distinct_artist"] = comp
        s["integrated_rows"] = len(integrated)
        s["overlap"] = {
            "confirmed_cleveland_creators_in_met": len(overlap),
            "of_which_with_qid": int((overlap["matched_qid"] != "").sum()),
        }

    with open(out / "match_summary.json", "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2, default=int)

    print(json.dumps(s, indent=2, default=int))
    print(f"\nWrote results to {out}/")


if __name__ == "__main__":
    main()
