"""Canonicalization of extracted names (roadmap P2-6).

Curated alias tables (NOT the on-hold checklist-DB fuzzy matching): map the
many ways brands/sets/subsets/teams appear on cards and labels onto one
canonical spelling, so both engines and the eval agree on names. Applied after
extraction + enrichment; unknown values pass through untouched.
"""

from app.models.card_info import CardInfo

_BRAND_CANON = {
    "upper deck": "Upper Deck",
    "ud": "Upper Deck",
    "topps": "Topps",
    "panini": "Panini",
    "donruss": "Donruss",
    "donruss playoff": "Playoff",
    "playoff": "Playoff",
    "leaf": "Leaf",
    "fleer": "Fleer",
    "bowman": "Bowman",
    "score": "Score",
}

_SET_CANON = {
    "threads": "Donruss Threads",
    "donruss threads": "Donruss Threads",
    "gridiron gear": "Gridiron Gear",
    "donruss gridiron gear": "Gridiron Gear",
    "national treasures": "National Treasures",
    "playoff national treasures": "National Treasures",
    "playoff nat.treas.": "National Treasures",
    "playoff nat. treas.": "National Treasures",
    "contenders": "Playoff Contenders",
    "playoff contenders": "Playoff Contenders",
    "leaf limited": "Leaf Limited",
    "exquisite collection": "Exquisite Collection",
    "upper deck exquisite collection": "Exquisite Collection",
    "collector's choice": "Collector's Choice",
    "coll. choice": "Collector's Choice",
    "collector's choice international": "Collector's Choice International",
    "coll. choice int'l": "Collector's Choice International",
    "collector's choice int'l": "Collector's Choice International",
    "sp rookie threads": "SP Rookie Threads",
}

_SUBSET_CANON = {
    "rookie patch autograph": "Rookie Patch Autograph",
    "rpa": "Rookie Patch Autograph",
    "rookie ticket": "Rookie Ticket",
    "star rookie": "Star Rookie",
    "star rookies": "Star Rookie",
    "gridiron kings": "College Gridiron Kings",
    "college gridiron kings": "College Gridiron Kings",
    "rookie gridiron gems": "Rookie Gridiron Gems",
    "jordan's journal": "Jordan's Journal",
    "rookie lettermen": "Rookie Lettermen",
    "sp rookie lettermen": "Rookie Lettermen",
    "college phenoms autos platinum spotlight": "College Phenoms Autos Platinum Spotlight",
    "rookie premiere autographs": "Rookie Premiere Autographs",
    "rookie premiere autograph": "Rookie Premiere Autographs",
}

# "SPANISH JORDAN'S JOURNAL" -> subset "Jordan's Journal" + language "es".
_LANGUAGE_QUALIFIERS = {
    "spanish": "es",
    "japanese": "ja",
    "german": "de",
    "french": "fr",
    "italian": "it",
    "portuguese": "pt",
}

_TEAM_CANON = {
    "georgia tech": "Georgia Tech Yellow Jackets",
    "yellow jackets": "Georgia Tech Yellow Jackets",
    "oklahoma": "Oklahoma Sooners",
    "sooners": "Oklahoma Sooners",
    "broncos": "Denver Broncos",
    "patriots": "New England Patriots",
    "cowboys": "Dallas Cowboys",
    "lions": "Detroit Lions",
    "vikings": "Minnesota Vikings",
    "falcons": "Atlanta Falcons",
    "bulls": "Chicago Bulls",
    "cavaliers": "Cleveland Cavaliers",
    "mariners": "Seattle Mariners",
}


def _canon(value: str | None, table: dict[str, str]) -> str | None:
    if not value:
        return value
    return table.get(value.strip().lower(), value)


def normalize_card(card: CardInfo) -> tuple[CardInfo, list[str]]:
    """Canonicalize names on a validated record; returns (card, changed_fields)."""
    record = card.model_dump(mode="json")
    changed: list[str] = []

    def apply(field: str, new_value: str | None) -> None:
        if new_value is not None and record.get(field) != new_value:
            record[field] = new_value
            changed.append(field)

    apply("brand", _canon(record.get("brand"), _BRAND_CANON))
    apply("set", _canon(record.get("set"), _SET_CANON))

    subset = record.get("subset")
    if subset:
        # Peel a leading language qualifier into the language field.
        first, _, rest = subset.strip().partition(" ")
        language = _LANGUAGE_QUALIFIERS.get(first.lower())
        if language and rest:
            subset = rest
            if not record.get("language") or record["language"] == "en":
                record["language"] = language
                changed.append("language")
        apply("subset", _canon(subset, _SUBSET_CANON))

    apply("team", _canon(record.get("team"), _TEAM_CANON))

    if changed:
        return CardInfo.model_validate(record), changed
    return card, changed
