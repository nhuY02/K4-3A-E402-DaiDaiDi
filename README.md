# VLearn hackathon prototype

This local-only prototype follows the VLearn flow:

1. The initial screen is the Home dashboard. Day01 and Day02 are the only active sessions because they are backed by the provided slide pack; later sessions are clearly marked `Chưa có data demo`.
2. Selecting a session opens its real 29-page lesson deck.
3. Slides are rendered server-side from the local PDFs with PyMuPDF and displayed as PNG images. There is no browser PDF viewer or iframe.
4. Previous/next, page count, zoom, notes, and cross-deck navigation are handled by explicit frontend state (`lesson`, `deckId`, `page`, `tutorOpen`).
5. Search indexes every extracted PDF page and combines `0.75 * semantic similarity + 0.25 * lexical relevance`. A relevance filter can return zero results; accepted results are limited to five.
6. “✨ Đặt câu hỏi với AI” opens the Tutor panel only when requested. The selected-text explanation interaction remains available in Tutor responses.
7. `/api/explain` receives a slide reference and resolves the real page text on the server before calling the existing `ai_service.explain_selection` function. The old synthetic `courseContexts` objects are no longer the live source of truth.

Normal Tutor chat now calls `POST /api/chat`, resolves the active slide on the server, adds a few directly relevant VLearn excerpts when available, and asks the configured OpenAI model for a concise Vietnamese answer. Selected-text explanation continues to use `POST /api/explain`. API keys, `.env`, logs, evaluation files, and the project directory are not served by the allowlisted loopback servers.

## Run

```powershell
python -m pip install -r requirements.txt
python server.py
```

In a second terminal:

```powershell
python frontend.py
```

Open <http://127.0.0.1:5173/>. Put `OPENAI_API_KEY` in the root `.env` only if semantic search or live selected-text explanation is needed; keyword search and the UI still work without it.

## Checks

```powershell
node --check app.js
python -m unittest discover -s tests -v
python eval/run_eval.py --validate-only
```

The CP3 Golden Set and historical comparison files are evidence artifacts and are intentionally not modified by this UX/retrieval change.
