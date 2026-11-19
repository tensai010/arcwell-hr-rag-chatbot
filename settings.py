"""Shared settings. Importing this module never calls an API."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')
EMBEDDING_MODEL = 'text-embedding-3-small'
EMBEDDING_DIMENSIONS = 300
COLLECTION_NAME = 'hr_docs_pages'
INDEX_PATH = BASE_DIR / 'data' / 'hr_index.json'
DEFAULT_RESPONSE_MODEL = 'gpt-4.1-mini'


class AssistantError(Exception):
    """A message safe to display to users."""


def make_client(api_key=None):
    from openai import OpenAI
    key = api_key or os.getenv('OPENAI_API_KEY')
    if not key or not key.strip():
        raise AssistantError('The assistant is not configured yet. Please ask the app owner to add an OpenAI API key.')
    return OpenAI(api_key=key, timeout=45.0, max_retries=1)
