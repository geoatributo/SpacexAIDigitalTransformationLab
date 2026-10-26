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

- `GET /questions` — 62 perguntas gold
- `GET /results/{id}` — contexto congelado + respostas da última run (`data/runs/phase1_*.json`)
- `POST /run/{id}` — volta a gerar os dois modelos no mesmo contexto
- `POST /evaluations` — guarda a avaliação humana em `data/evaluations.json`
- `GET /evaluations.csv` — exportação
- `POST /chat` e `POST /chat/stream` — pergunta livre

`VITE_API_URL` define o endereço da API (omissão: `http://localhost:8000`). As chaves ficam no `.env`, nunca no código.
