"""Explicit offline fixture loader; never called as a BigQuery fallback."""

import json
import os
from pathlib import Path

from backend.core.context_contract import FinancialContext
from backend.data.bigquery_context import DataProviderError
from backend.data.golden_context import context_from_snapshot, validate_snapshot


FIXTURE_PATH = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "golden_persona.json"


def load_golden_fixture() -> FinancialContext:
    """Load supplied test facts, without cloud calls or fabricated row dates/counts."""
    if os.getenv("K_SERVICE"):
        raise DataProviderError("golden_fixture_forbidden_in_cloud")
    try:
        snapshot = validate_snapshot(json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))
        if snapshot.origin != "user_supplied_hackathon_snapshot":
            raise ValueError("Fixture origin is not a real query")
    except (OSError, ValueError, TypeError):
        raise DataProviderError("golden_fixture_unavailable") from None
    return context_from_snapshot(snapshot)
