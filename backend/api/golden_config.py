"""Fixed synthetic demo identity, never selected from a client or model payload."""
import os
from datetime import date
from fastapi import HTTPException

GOLDEN_USER_ID = '6491f4a4-67dc-49de-a38a-cf655ff77c33'
GOLDEN_REFERENCE_DATE = date(2025, 9, 30)
GOLDEN_ALIAS = 'persona-a'  # Compatibility alias, not a persona selection menu.


def golden_enabled() -> bool:
    return bool(os.getenv('DEMO_USER_ID') or os.getenv('DEMO_REFERENCE_DATE')
                or os.getenv('DATA_PROVIDER') == 'golden_fixture')


def validate_golden_config() -> None:
    if (os.getenv('DEMO_MODE', '').lower() != 'true'
            or os.getenv('DEMO_USER_ID') != GOLDEN_USER_ID
            or os.getenv('DEMO_REFERENCE_DATE') != GOLDEN_REFERENCE_DATE.isoformat()
            or os.getenv('DATA_PROVIDER') not in {'bigquery', 'golden_fixture'}
            or (os.getenv('K_SERVICE') and (os.getenv('DATA_PROVIDER') != 'bigquery'
                                          or os.getenv('AGENT_PROVIDER') != 'gemini'))):
        raise HTTPException(503, detail={'code':'golden_demo_not_configured',
            'message':'Configuração da golden persona incompleta; nenhum provider foi substituído.'})
