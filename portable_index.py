"""Restore precomputed vectors without an embedding API call."""
import hashlib
import json
import math
from pathlib import Path
import chromadb
from settings import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, INDEX_PATH


def validate_index(data):
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('Unsupported index format.')
    if data.get('embedding_model') != EMBEDDING_MODEL or data.get('dimensions') != EMBEDDING_DIMENSIONS:
        raise ValueError('Embedding model or dimensions do not match.')
    fields = ['ids', 'documents', 'metadatas', 'embeddings']
    if any(not isinstance(data.get(field), list) for field in fields):
        raise ValueError('Missing index arrays.')
    count = len(data['ids'])
    if any(len(data[field]) != count for field in fields):
        raise ValueError('Index arrays have different lengths.')
    if any(not isinstance(i, str) or not i for i in data['ids']) or len(set(data['ids'])) != count:
        raise ValueError('Invalid or duplicate IDs.')
    for document, metadata, vector in zip(data['documents'], data['metadatas'], data['embeddings']):
        if not isinstance(document, str) or not document.strip():
            raise ValueError('Empty document.')
        if not isinstance(metadata, dict) or not metadata:
            raise ValueError('Invalid metadata.')
        if any(not isinstance(k, str) or not isinstance(v, (str, int, float, bool)) for k, v in metadata.items()):
            raise ValueError('Metadata must contain scalar values.')
        if not isinstance(vector, list) or len(vector) != EMBEDDING_DIMENSIONS:
            raise ValueError('Invalid vector dimensions.')
        if any(type(v) not in (float, int) or not math.isfinite(v) for v in vector):
            raise ValueError('Invalid vector values.')
    return data


def load_collection(index_path=INDEX_PATH):
    raw = Path(index_path).read_bytes()
    data = validate_index(json.loads(raw))
    name = 'hr-' + hashlib.sha256(raw).hexdigest()[:24]
    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection(name, embedding_function=None)
    if collection.count() != len(data['ids']) and data['ids']:
        for start in range(0, len(data['ids']), 1000):
            collection.upsert(**{field: data[field][start:start + 1000]
                                 for field in ['ids', 'documents', 'metadatas', 'embeddings']})
    return collection
