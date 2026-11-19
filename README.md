# Arcwell HR Assistant

A Streamlit chatbot over the fictional Arcwell HR handbook. Reuses the original
pypdf chunker, OpenAI embeddings, Chroma search and Responses API. No LangChain.

## Run locally (PowerShell)

From this workspace, using the existing environment:

```powershell
cd "C:\Users\Ashwin Kumar\OneDrive\Desktop\AI_Bootcamp\AI_Bootcamp_Namaste_SQL\RAG_DAY01"
& ..\..\.venv\Scripts\python.exe -m pip install -r requirements.txt
& ..\..\.venv\Scripts\python.exe -m streamlit run app.py
```

Your existing `.env` is read locally and has not been changed. For a fresh clone
with Python 3.13 installed:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env locally and set your API key; never commit it.
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Environment variables override `.env`. Alternatively use `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "your-private-key"
OPENAI_RESPONSE_MODEL = "gpt-4.1-mini"
```

The model is configurable; use a Responses-compatible model available to your
OpenAI project. The default preserves the original `gpt-4.1-mini` model.

## How the app works

- `chunking.py`: original fixed 500-character chunks with 100-character overlap;
  preserves document names and 1-based page numbers.
- `ingestion.py`: explicit offline ingestion, batched `text-embedding-3-small`
  calls at **300 dimensions**, then local Chroma upserts. No import-time calls.
- `export_index.py`: exports precomputed embeddings, text, IDs and metadata from
  the local `hr_docs_pages` collection into `data/hr_index.json` without API calls.
- `portable_index.py`: validates index shape/model/dimensions and loads an
  `EphemeralClient` collection with embedding functions disabled.
- `retrieval.py`: embeds the question, retrieves up to **5** chunks, and returns
  `(answer, sources)` using the Responses API. A small amount of conversation
  history helps with follow-up questions. History is not policy evidence.
- `app.py`: caches only the shared handbook collection with `st.cache_resource`.
  Chat history lives in each browser session's `st.session_state`. New Chat and
  Clear Chat both reset that session; neither deletes the shared index.

The bundled index contains 115 existing vectors. **Startup and reruns make no
embedding calls.** Each submitted question makes one query-embedding call and
one answer call. Cloud restarts reload the bundled JSON into memory; no writable
or persistent disk database is needed. The PDF is optional at runtime.

Source panels show retrieved evidence, not a claim that every retrieved chunk
was cited in the answer. Sections appear only when metadata contains `section`;
the original index contains document/page metadata, so no section names are
fabricated. Grounding instructions require abstention for missing information;
model answers still need evaluation and cannot be guaranteed hallucination-free.

## Refresh the handbook (offline only)

If the existing local database is valid, export it directly:

```powershell
& ..\..\.venv\Scripts\python.exe export_index.py
```

Only after changing the fictional PDF, run ingestion first (this makes billable
embedding calls), then export:

```powershell
& ..\..\.venv\Scripts\python.exe ingestion.py
& ..\..\.venv\Scripts\python.exe export_index.py
```

Commit the refreshed JSON with the app. Never run ingestion during Streamlit
startup. Legacy learning files (`main.py`, `vector_db.py`, `get_data_from_vdb.py`)
are separate exercises, are not imported by the app, and use different dimensions.
`requirements.txt` is the deployment dependency list; `req.txt` is the old exercise list.

## Validation

```powershell
& ..\..\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests use real in-memory Chroma and the exported index, but mock OpenAI calls.
They verify PDF/index equality, 300 dimensions, top-five retrieval, empty and
small collections, API error sanitization, missing credentials, UI chat/reset
behavior, and absence of startup API calls. No test requires an API key or spends
API credits. Live answer quality and deployment must be checked with your account.

## GitHub deployment preparation

Create a dedicated repository from this `RAG_DAY01` folder. This keeps unrelated
bootcamp exercises and parent `.env` files out of the app repository. The parent
folder currently has an ignore-all `.gitignore`; a standalone repository here
avoids changing that unrelated configuration.

Create an empty GitHub repository named `arcwell-hr-assistant`, then run:

```powershell
git init
git branch -M main
git add app.py chunking.py ingestion.py retrieval.py settings.py portable_index.py export_index.py requirements.txt README.md .gitignore .env.example .streamlit/config.toml data/hr_index.json tests/test_app.py hr_policy.pdf
git diff --cached --stat
git status --short
# Review staged content. Only the fictional handbook belongs in this repository.
git commit -m "Build Arcwell HR Assistant"
git remote add origin https://github.com/YOUR_USERNAME/arcwell-hr-assistant.git
git push -u origin main
```

The JSON contains handbook text as well as vectors. Only publish fictional data.
`.env`, local Chroma storage, secrets, caches and virtual environments are ignored.
No repository has been created or pushed automatically.

## Streamlit Community Cloud

1. Sign in at https://share.streamlit.io and choose **Create app**.
2. Select your GitHub repository, branch `main`, and main file `app.py`.
3. Under **Advanced settings**, choose **Python 3.13** (the locally tested version).
4. Paste the two settings from the TOML example into the **Secrets** field using
   your real API key. Do not put credentials in GitHub.
5. Deploy. The app installs `requirements.txt` and restores `data/hr_index.json`.
6. Check one suggested question, its sources, a follow-up and an unsupported
   policy question. Confirm the last question does not invent policy details.

If using a larger repository instead, the entry point is `RAG_DAY01/app.py` and
requirements stay beside it. The standalone repository above is simplest.
For a public app, requests use the owner's OpenAI account; configure usage limits
appropriate for a demo. Do not enter or publish real employee information.

Official references:
- OpenAI model: https://developers.openai.com/api/docs/models/gpt-4.1-mini
- Streamlit deployment: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
