# airtable_service.py
"""
Fable Airtable Service - Direct HTTP Client using your apres-ARM PAT.
"""
import os
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger("apres.pipeline.airtable")

AIRTABLE_PAT = os.getenv("AIRTABLE_API_KEY") or os.getenv("AIRTABLE_PAT")
BASE_ID = "appMriWKZylklqFDe"  # Apres Ledger base

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

def create_record(table_name: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates a single record in the specified table.
    """
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_name}"
    payload = {"fields": fields}
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        if response.status_code == 200:
            logger.info(f"Successfully created record in {table_name}")
            return response.json()
        else:
            logger.error(f"Failed: Status {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error during Airtable write to {table_name}: {str(e)}")
        return None