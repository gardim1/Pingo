# Pingo

Pingo é um agente financeiro criado para a Batalha de Agentes Itaú + Google.
Ele usa contexto financeiro, cálculo determinístico e IA conversacional para
ajudar o usuário a entender o impacto futuro de decisões financeiras.

## Problema

O banco normalmente mostra o passado financeiro. O Pingo ajuda a responder:
“o que acontece se eu fizer isso agora?”

## Principais capacidades

- análise contextual;
- simulação de compra;
- comparação de cenários;
- golden persona sintética;
- Supervisor opt-in;
- cálculo financeiro determinístico;
- Gemini para interpretação/conversa;
- BigQuery para contexto;
- Cloud Run.

## Arquitetura resumida

```
Browser
  → pingo-frontend
  → server-side S2S
  → pingo-backend privado
  → BigQuery + Engine + Gemini
```

## Stack

- React
- TypeScript
- Vite
- Node/Express
- FastAPI/Python
- Google Cloud Run
- BigQuery
- Google ADK
- Gemini via Vertex AI

## Estrutura

- `backend/`: API FastAPI, engine financeiro, agente, adapters de dados e guardrails.
- `frontend/`: app React/Vite com servidor Node/Express que chama o backend server-side.
- `tests/`, `scripts/`: testes, evals e smoke tests.
- `contracts/`: schemas JSON da resposta de decisão.
- `docs/`: especificação, handoffs de API, BigQuery, deploy e relatórios de evals. Destaques para a submissão: [`docs/RACIONAL_EXPERIENCIA.md`](docs/RACIONAL_EXPERIENCIA.md) (racional de prototipação e UX), [`docs/DESENHO_SOLUCAO.md`](docs/DESENHO_SOLUCAO.md) (arquitetura, engenharia e ciência de dados) e [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) (componentes, integrações e decisões técnicas).

## Demo pública

Frontend: https://pingo-frontend-575520783518.us-central1.run.app

Backend: Cloud Run privado.

## Rodar localmente (backend offline)

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
$env:DEMO_MODE = 'true'
$env:DEMO_USER_ID = '<SYNTHETIC_DEMO_USER_ID>'
$env:DEMO_REFERENCE_DATE = '2025-09-30'
$env:DATA_PROVIDER = 'golden_fixture'
$env:AGENT_PROVIDER = 'demo'
$env:SAFETY_PROVIDER = 'local'
./.venv/Scripts/python.exe -m backend
./.venv/Scripts/python.exe -m pytest -q
```

Veja `.env.example` e `docs/API_BACKEND.md` para as demais variáveis.

## Status

MVP de hackathon.

## Dados

Os dados utilizados na demonstração são sintéticos e fornecidos no contexto do desafio.

## Segurança

- backend privado;
- autenticação service-to-service;
- `user_id` imposto no servidor;
- queries parametrizadas/read-only;
- cálculos financeiros fora do LLM;
- guardrails locais.
