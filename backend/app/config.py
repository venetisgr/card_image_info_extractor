"""Runtime configuration for the extraction service.

Secrets live in environment variables (or a local git-ignored ``.env`` file) —
never in code or in the repo. See resources.md (secrets strategy).
"""

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
SHARED_DIR = REPO_ROOT / "shared"
SCHEMA_PATH = SHARED_DIR / "schema" / "card_info.schema.json"
PLACEHOLDER_PATH = SHARED_DIR / "templates" / "card_info_placeholder.json"
EXAMPLE_PATH = SHARED_DIR / "examples" / "graded_relic_example.json"

# Model tiering (roadmap P1-7). Aliases resolve to current model IDs; a full
# model id is also accepted as-is.
MODEL_ALIASES = {
    "opus": "claude-opus-4-8",
    "sonnet": "claude-sonnet-5",
    "haiku": "claude-haiku-4-5",
}
DEFAULT_MODEL = MODEL_ALIASES["opus"]

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # per image
MAX_IMAGE_LONG_EDGE = 2576  # Claude vision native-resolution ceiling
JPEG_QUALITY = 90
MAX_OUTPUT_TOKENS = 8192

# Indicative $/1M-token prices for the CLI cost readout (input, output).
MODEL_PRICES_PER_MTOK = {
    "claude-opus-4-8": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
}


def load_dotenv(path: Path | None = None) -> None:
    """Load KEY=VALUE lines from a .env file into os.environ (no overrides)."""
    env_path = path or (BACKEND_DIR / ".env")
    if not env_path.is_file():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def resolve_model(name: str | None) -> str:
    """Resolve a tier alias ('opus'/'sonnet'/'haiku') or pass through a model id."""
    if not name:
        return DEFAULT_MODEL
    return MODEL_ALIASES.get(name.lower().strip(), name.strip())
