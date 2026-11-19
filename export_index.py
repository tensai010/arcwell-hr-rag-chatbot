"""Export an existing local Chroma collection; makes no OpenAI requests."""
import argparse
import json
from pathlib import Path
import chromadb
from portable_index import validate_index
from settings import BASE_DIR, COLLECTION_NAME, EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, INDEX_PATH


def export_index(db_path=BASE_DIR / 'chroma_db', output=INDEX_PATH):
    db_path, output = Path(db_path), Path(output)
    if not (db_path / 'chroma.sqlite3').is_file():
        raise ValueError('No existing Chroma database found. Run ingestion.py locally first.')
    collection = chromadb.PersistentClient(path=str(db_path)).get_collection(COLLECTION_NAME)
    if not collection.count():
        raise ValueError('The collection is empty. Run ingestion.py locally first.')
    records = collection.get(include=['documents', 'metadatas', 'embeddings'])
    data = dict(schema_version=1, embedding_model=EMBEDDING_MODEL,
                dimensions=EMBEDDING_DIMENSIONS, ids=records['ids'],
                documents=records['documents'], metadatas=records['metadatas'],
                embeddings=records['embeddings'].tolist())
    validate_index(data)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    temporary.replace(output)
    return len(data['ids'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db-path', type=Path, default=BASE_DIR / 'chroma_db')
    parser.add_argument('--output', type=Path, default=INDEX_PATH)
    args = parser.parse_args()
    try:
        count = export_index(args.db_path, args.output)
        print(f'Exported {count} precomputed 300-dimensional vectors to {args.output}')
    except Exception:
        raise SystemExit('Export failed. Check that the HR collection exists, is nonempty and uses 300-dimensional vectors.') from None
