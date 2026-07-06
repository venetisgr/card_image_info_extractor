"""Verification/enrichment of extracted records (roadmap P2-2).

Policy (architecture_components.md §10): verified API data beats model output.
For a graded PSA card whose cert number was read from the label, the PSA
public API record overrides the extracted descriptive fields, verified fields
get confidence 1.0, and the raw PSA record is preserved in `raw_output` for
audit.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.models.card_info import CardInfo
from app.services.psa import PSAClient, PSAError

# PSA `Category` → our sport enum.
_SPORT_WORDS = {
    "baseball": "baseball",
    "basketball": "basketball",
    "football": "football",
    "hockey": "hockey",
    "soccer": "soccer",
}


@dataclass
class EnrichmentOutcome:
    attempted: bool = False
    verified: bool = False
    changed_fields: list[str] = field(default_factory=list)
    note: str | None = None


def _sport_from_category(category: str | None) -> str | None:
    lowered = (category or "").lower()
    for word, sport in _SPORT_WORDS.items():
        if word in lowered:
            return sport
    return "other" if lowered.strip() else None


def _grade_number(value) -> float | None:
    match = re.search(r"\d+(\.\d+)?", str(value or ""))
    return float(match.group()) if match else None


def _tidy(value) -> str | None:
    text = str(value or "").strip()
    return text or None


def map_psa_record(psa: dict) -> dict:
    """Flatten a PSACert record into CardInfo dot-path -> verified value."""
    grade_label = _tidy(psa.get("GradeDescription"))
    year = _tidy(psa.get("Year"))
    brand = _tidy(psa.get("Brand"))
    subject = _tidy(psa.get("Subject"))
    variety = _tidy(psa.get("Variety"))

    mapped = {
        "year": year,
        "brand": brand.title() if brand else None,
        # PSA's Brand line is the set description (e.g. "PLAYOFF NATIONAL
        # TREASURES"); proper brand/set splitting arrives with the checklist DB.
        "set": brand.title() if brand else None,
        "subset": variety,
        "player_name": subject.title() if subject else None,
        "card_number": _tidy(psa.get("CardNumber")),
        "sport": _sport_from_category(_tidy(psa.get("Category"))),
        "graded.grading_company": "PSA",
        "graded.grade": _grade_number(psa.get("CardGrade") or grade_label),
        "graded.grade_label": grade_label,
        "graded.cert_number": _tidy(psa.get("CertNumber")),
    }
    return {path: value for path, value in mapped.items() if value is not None}


def _apply(record: dict, path: str, value) -> bool:
    parts = path.split(".")
    target = record
    for part in parts[:-1]:
        if target.get(part) is None:
            target[part] = {}
        target = target[part]
    if target.get(parts[-1]) == value:
        return False
    target[parts[-1]] = value
    return True


def apply_psa_record(card: CardInfo, psa: dict) -> tuple[CardInfo, list[str]]:
    """Override the extracted record with PSA's verified fields."""
    record = card.model_dump(mode="json")
    changed = []
    for path, value in map_psa_record(psa).items():
        if _apply(record, path, value):
            changed.append(path)
        record["per_field_confidence"][path] = 1.0

    raw = record.get("raw_output") or {}
    raw["verification"] = {
        "source": "psa_public_api",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "psa_cert": psa,
    }
    record["raw_output"] = raw
    return CardInfo.model_validate(record), changed


def enrich_card(card: CardInfo, psa_client: PSAClient) -> tuple[CardInfo, EnrichmentOutcome]:
    """Verify a graded PSA card via cert lookup; other cards pass through.

    Never raises: lookup problems are reported in the outcome note so an
    enrichment hiccup can't fail an otherwise-good extraction.
    """
    outcome = EnrichmentOutcome()
    graded = card.graded
    if (
        card.card_type.value != "graded"
        or graded is None
        or graded.grading_company is None
        or graded.grading_company.value != "PSA"
        or not (graded.cert_number or "").strip()
    ):
        outcome.note = "not a PSA-graded card with a cert number"
        return card, outcome
    if not psa_client.available:
        outcome.note = "PSA token not configured; skipped"
        return card, outcome

    outcome.attempted = True
    try:
        psa = psa_client.get_cert(graded.cert_number)
    except PSAError as exc:
        outcome.note = str(exc)
        return card, outcome
    if psa is None:
        outcome.note = f"PSA has no record for cert {graded.cert_number}"
        return card, outcome

    enriched, changed = apply_psa_record(card, psa)
    outcome.verified = True
    outcome.changed_fields = changed
    outcome.note = f"verified against PSA cert {graded.cert_number}"
    return enriched, outcome
