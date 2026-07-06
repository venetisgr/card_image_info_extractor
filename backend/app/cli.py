"""CLI wrapper for quick local extractions (roadmap P1-8).

Usage (from backend/, venv active, ANTHROPIC_API_KEY in env or backend/.env):
    python -m app.cli path/to/front.jpg [path/to/back.jpg] [--model opus|sonnet|haiku|<id>] [--out card.json]
"""

import argparse
import json
import sys
import time
from pathlib import Path

from app.config import MODEL_PRICES_PER_MTOK, load_dotenv, resolve_model
from app.services.enrich import enrich_card
from app.services.extractor import CardExtractor
from app.services.images import preprocess_image
from app.services.psa import PSAClient


def _estimate_cost(usage) -> float | None:
    prices = MODEL_PRICES_PER_MTOK.get(usage.model)
    if not prices:
        return None
    in_price, out_price = prices
    return (
        usage.input_tokens * in_price
        + usage.cache_creation_input_tokens * in_price * 1.25
        + usage.cache_read_input_tokens * in_price * 0.10
        + usage.output_tokens * out_price
    ) / 1_000_000


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract CardInfo from card photos via Claude.")
    parser.add_argument("front", type=Path, help="photo of the card front")
    parser.add_argument("back", type=Path, nargs="?", default=None, help="photo of the back")
    parser.add_argument("--model", default=None, help="opus | sonnet | haiku | full model id")
    parser.add_argument("--out", type=Path, default=None, help="write the CardInfo JSON here")
    parser.add_argument(
        "--no-enrich", action="store_true", help="skip PSA cert verification for graded PSA cards"
    )
    args = parser.parse_args(argv)

    load_dotenv()
    model = resolve_model(args.model)
    front = preprocess_image(args.front.read_bytes())
    back = preprocess_image(args.back.read_bytes()) if args.back else None

    extractor = CardExtractor()
    start = time.perf_counter()
    result = extractor.extract(front, back, model=model)
    if not args.no_enrich:
        card, outcome = enrich_card(result.card, PSAClient())
        result.card = card
        if outcome.note:
            print(f"[psa] {outcome.note}"
                  + (f" (updated: {', '.join(outcome.changed_fields)})"
                     if outcome.changed_fields else ""),
                  file=sys.stderr)
    elapsed = time.perf_counter() - start

    payload = json.dumps(result.card.model_dump(mode="json"), indent=2)
    if args.out:
        args.out.write_text(payload + "\n")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(payload)

    u = result.usage
    cost = _estimate_cost(u)
    print(
        f"[{u.model}] {elapsed:.1f}s, attempts={u.attempts}, "
        f"in={u.input_tokens} out={u.output_tokens} "
        f"cache_write={u.cache_creation_input_tokens} cache_read={u.cache_read_input_tokens}"
        + (f", ~${cost:.4f}" if cost is not None else ""),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
