# Goldilocks RAG

Comparação lado a lado (xAI vs Gemini) e chat livre sobre o RAG já carregado.

## Correr

Na raiz do repositório:

```text
py -m pip install -r requirements.txt
$env:PYTHONPATH="src"
py -m uvicorn lab.app:app --reload --host 127.0.0.1 --port 8000
```

Noutro terminal:

```text
cd web
npm install
npm run dev
```

Abrir http://localhost:5173. A API está em http://localhost:8000.

- `POST /session` — declaração do nome e modo (`rate` ou `metrics_only`)
- `GET /dashboard` — cartões das métricas da última run/eval
- `GET /blind/cases/{id}` — respostas A/B às cegas (sem nomes dos sistemas)
- `POST /human/ratings` — notas 0–10 por resposta; Firestore (`FIREBASE_PROJECT_ID`)
- `GET /human/export.csv` — descarga pública com `rater_id`, não o nome
- `GET /questions` / `GET /results/{id}` — leitura técnica identificada (só no modo métricas)
- `POST /chat` — pergunta livre (só no modo métricas)

`VITE_API_URL` vazio (defeito) usa o mesmo origin — em `npm run dev` o proxy do Vite, no Cloud Run a própria API. As chaves ficam no `.env`, nunca no código.
