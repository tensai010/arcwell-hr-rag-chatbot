from pypdf import PdfReader
from pathlib import Path

doc_path = r'AI_Bootcamp_Namaste_SQL\RAG_DAY01\hr_policy.pdf'



def create_chunks(doc_path,chunk_size=500,overlap_size=100):
    if not 0 <= overlap_size < chunk_size:
        raise ValueError('invalid chunk size or overlap')
    
    reader = PdfReader(doc_path)

    chunks = []
    ids = []
    metadatas = []

    for page_number,page in enumerate(reader.pages,start=1):
        text = page.extract_text() or ''
        start = 0
        chunk_id = 1

        while start < len(text):
            end = min(start + chunk_size , len(text))

            chunk = text[start:end]

            if chunk.strip():
                chunks.append(chunk)

                ids.append(
                    f'{Path(doc_path).stem}_p{page_number}_c{chunk_id}'
                )

                metadatas.append({
                    'doc_name': Path(doc_path).name,
                    'page': page_number,
                    'version':1
                })

            chunk_id +=1

            if end == len(text):
                break

            start = end - overlap_size

    return chunks,ids,metadatas

