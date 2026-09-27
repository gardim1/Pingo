# Revisão independente do backend

2026-09-26. Revisão de código e reproduções locais, sem chamadas Google, Docker, deploy ou alterações no código pelo revisor. O baseline é o index Git, pois ainda não há commit inicial. Escopo: agent/API/models/core, data/safety, testes e empacotamento; especificação v2 e requisitos do workshop foram considerados.

## Resultado da rechecagem

Os cinco achados foram corrigidos pelo integrador e receberam testes de regressão. **Nenhum achado demonstrado permanece aberto nesta revisão.** A rechecagem independente final executou `.\.venv\Scripts\python.exe -m pytest tests/test_agent.py tests/test_chat.py -q`: **23 passed**, com um aviso de depreciação do TestClient/Starlette. Essa contagem cobre a rechecagem focal; a suíte completa pertence ao relatório consolidado do integrador.

| Prioridade | Achado inicial / reprodução | Situação |
|---|---|---|
| P1 | `backend/agent/intent.py`: “iPhone em 10x de R$ 100,00 sem entrada, primeira em 2026-10-01” produzia HTTP 200/ready e total de 10000 centavos, confundindo valor por parcela com total. | Corrigido: prefixos de parcela e sufixos `por mês`/`/parcela` não viram preço total; pedem confirmação. |
| P2 | `backend/agent/intent.py`: `R$ 10.0000` era parcialmente reconhecido como R$ 10, produzindo total de 1000 centavos. | Corrigido: validação do token monetário inteiro. |
| P2 | `backend/agent/intent.py`: “primeira em 2026-10-01 ou primeira em 2026-12-01” escolhia a primeira alternativa sem confirmação. | Corrigido: múltiplas datas deixam o campo ausente. |
| P2 | `backend/agent/provider.py`: o finally fechava somente o cliente síncrono, embora ADK use o assíncrono. Cliente real capturado num teste sem rede estava `sync closed=True`, `async closed=False`. | Corrigido: `await client.aio.aclose()` e fechamento síncrono em finally aninhado; teste retém o cliente para não confundir coleta de lixo com cleanup. |

## Rechecagem de alterações em conversa

**P2 corrigido — atualização não reconhecida conservava condição antiga**, `backend/agent/intent.py`, inicialização por `previous` e ramos sem extração. Com decisão anterior completa `{total_price_cents:100000, upfront_cents:0, installment_count:10, first_due_date:"2026-10-01"}`, “Agora custa R$ 2.000”, “Mudar entrada para R$ 200” e “Mude a primeira para novembro” conservavam os campos antigos e podiam produzir `ready` sem aplicar a alteração. A correção invalida o campo mencionado antes de extrair seu novo valor. Reproduções independentes após a correção: preço = 200000 centavos; entrada = 20000 centavos; data = null; “Mudar para vinte parcelas” = quantidade null. Os demais campos são preservados, e campos null fazem o engine perguntar.

## Controles inspecionados e limites

- Identidade imposta por allowlist/configuração do servidor; o schema do modelo não contém identidade, SQL ou valores financeiros. Catálogo fechado, argumentos vazios validados e orçamento de chamadas.
- Engine usa centavos e datas; contexto histórico não preenche saldo atual nem agenda futura. Conciliação explícita compra/fatura exige vínculo validado.
- Consentimento falso retorna antes de providers; erros cloud são explícitos e não selecionam fixture. Textos do modelo não são enviados à interface.
- SQL fixo e parametrizado, dry-run, teto de bytes, timeout e agregados limitados. Logs próprios omitem mensagens e payloads financeiros. Empacotamento usa allowlist de arquivos e entrypoint com PORT.

Esses controles são evidência local, não certificação de segurança. Gemini/ADK foram exercitados com substituição do transporte/modelo e sem inferência real; aceitação do schema pelo endpoint, modelo/região/ADC continuam por validar. BigQuery real, Model Armor real e build/execução Docker/Cloud Run também não foram validados nesta revisão. A indisponibilidade do ambiente cloud é uma pendência de integração, não um bug demonstrado.
