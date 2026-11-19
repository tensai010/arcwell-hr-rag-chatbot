"""Offline ingestion only: python ingestion.py. Never runs on import."""
import chromadb
from chunking import create_chunks
from settings import (BASE_DIR, COLLECTION_NAME, EMBEDDING_DIMENSIONS,
                      EMBEDDING_MODEL, make_client)


def batch_embeddings(texts, client=None):
    if not texts:
        return []
    client = client or make_client()
    embeddings = []
    for start in range(0, len(texts), 64):
        response = client.embeddings.create(
            model=EMBEDDING_MODEL, input=texts[start:start + 64],
            dimensions=EMBEDDING_DIMENSIONS)
        embeddings.extend(item.embedding for item in sorted(response.data, key=lambda item: item.index))
    return embeddings


def get_embeddings(text, client=None):
    return batch_embeddings([text], client)[0]


def ingest_document(doc_path=BASE_DIR / 'hr_policy.pdf'):
    chunks, ids, metadatas = create_chunks(doc_path, chunk_size=500, overlap_size=100)
    if not chunks:
        raise ValueError('The PDF contains no extractable text.')
    embeddings = batch_embeddings(chunks)
    db = chromadb.PersistentClient(path=str(BASE_DIR / 'chroma_db'))
    collection = db.get_or_create_collection(COLLECTION_NAME, embedding_function=None)
    old_ids = set(collection.get()['ids'])
    collection.upsert(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)
    obsolete = old_ids - set(ids)
    if obsolete:
        collection.delete(ids=list(obsolete))
    return collection.count()


if __name__ == '__main__':
    try:
        print(f'Documents stored in ChromaDB: {ingest_document()}')
    except Exception:
        raise SystemExit('Ingestion failed. Check the PDF, API credentials, connection and quota.') from None
