# Pingo — publicar a nova revisão golden no Cloud Run

Atualizado em **2026-09-27**. Este roteiro continua o backend em `C:\Users\Eliane Gardim\Documents\Pingo` ou sua cópia aprovada no Cloud Shell. Leia AGENTS.md, STATUS-CORE.md, GOLDEN_PERSONA.md, API_BACKEND.md e BIGQUERY_HANDOFF.md. O pedido mais recente autoriza a golden persona e uma nova publicação pelo ambiente GCP já autorizado; supera o antigo limite de primeiro core local.

**Versão anterior já publicada; nova golden ainda NÃO publicada.** Serviço `pingo-backend`, projeto `batalha-time-08-g7ha`, região `us-central1`. URL anterior: `https://pingo-backend-575520783518.us-central1.run.app`. Revisão registrada: `pingo-backend-00001-l22`, 100% de tráfego. Evidência anterior em `work/cloud-run-smoke.json`, PASS 2026-09-27T02:24:38Z. Revalidar configuração/tráfego atuais; não presumir que permaneceram iguais.

**Critério obrigatório:** nova revisão golden + URL real + health 200 + jornada golden com Gemini e BigQuery reais nessa URL. Handoff, testes offline e a revisão anterior não cumprem o aceite da atualização. Não adicionar features, frontend, catálogo ou refactor. Não alterar IAM/faturamento nem tornar o serviço público.

## Continuação executada — 27/09/2026, 06:08 BRT

**VERIFICADO:** ADC com TLS válido usando confiança nativa do Windows; dry-run e SQL golden real (job `9f752879-64f2-4e0c-80f8-56a0233dfc0c`); jornada HTTP local completa com BigQuery e Gemini `gemini-3.8-flash` reais, oito turnos e Supervisor/replay, 13 respostas HTTP 200. Salário/parcelas/margens/centavos conferidos pelo harness existente, sem fixture. Os 147 testes, 18 evals e 23 golden foram reexecutados após a correção e passaram; dependências íntegras.

**Correção mínima:** uma linha em `backend/agent/provider.py`, `max_output_tokens=512` → `2048`. O limite anterior gerava `MAX_TOKENS` e JSON incompleto na golden real. Após a mudança, as oito chamadas terminaram em `STOP`. Engine, SQL, API, contratos e guardrails preservados. O teto maior pode aumentar consumo/latência potencial; timeout e chamada única permanecem.

**Cloud Run atual revalidado:** URL canônica `https://pingo-backend-uahbqqbh3a-uc.a.run.app`, revisão anterior `pingo-backend-00001-l22`, 100% do tráfego no snapshot; health autenticado 200, anônimo 403. **Nenhuma nova build, revisão ou promoção realizada.** A validação golden ocorreu com ADC local; ainda falta a nova revisão com identidade runtime e smoke HTTPS.

**BLOQUEIO IAM:** `folders/900300571186:getIamPolicy` retornou 403 `PERMISSION_DENIED` / `IAM_PERMISSION_DENIED`; operação exige `resourcemanager.folders.getIamPolicy`. Serviço/projeto sem bindings públicos e invoker IAM habilitado, mas ausência de grants herdados não pôde ser comprovada. O handoff exige essa comprovação. Não houve tentativa de deploy negada nem alteração de IAM. Um responsável com acesso deve verificar a política da pasta e dos ancestrais aplicáveis, ou continuar no ambiente autorizado a realizar essa leitura; depois retomar build/candidata/smoke/promoção. Não conceder acesso público.

Detalhes e limites: [EXECUCAO_GOLDEN_REAL_2026-09-27.md](EXECUCAO_GOLDEN_REAL_2026-09-27.md). Evidência consolidada: `work/golden-continuation-evidence-20260927.json`. Integração preparada em [FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md); nenhum frontend/proxy encontrado nesta cópia. Safety local preservada; Model Armor remoto não validado.

## 1. Estado local e sequência

147 testes PASS, 18 evals anteriores PASS, 23 golden PASS e pip check íntegro reexecutados. O SQL golden/CLT e a jornada HTTP local agora passaram com BigQuery/Gemini reais; detalhes na continuação acima. A confiança TLS foi resolvida somente no processo local, usando o trust store nativo do Windows, sem desativar certificados. `gcloud`/`bq`/Docker continuam ausentes do PATH; foram utilizadas APIs oficiais com ADC. Nenhuma publicação realizada: bloqueio atual é a leitura IAM ancestral 403. Revalidar os pré-requisitos ao retomar.

Executar na ordem: setup do participante → projeto/ADC → BigQuery golden real → Gemini pelo backend → safety/Model Armor permitido → testes/build/smoke da imagem → revisão candidata → URL/health/jornada → tráfego → repetir smoke e registrar evidência. Se algo depender de login/MFA/IAM, registrar bloqueio e concluir apenas passos independentes.

A arquitetura permanece FastAPI, um agente Gemini/ADK, tools fechadas, engine determinístico, adapter BigQuery e guardrails. Plano/consentimento usam snapshots existentes; nenhuma persistência/notificação nova. A fixture golden fica em testes e não entra na imagem; K_SERVICE recusa provider golden_fixture/agente demo no modo golden. `DEMO_MODE=true` não significa fixture: `DATA_PROVIDER=bigquery` é obrigatório na publicação.

## 2. Setup do participante e autenticação

Fonte já localizada: guia dos organizadores `C:\Users\Eliane Gardim\Downloads\guia_interativo_batalha_de_agentes-6.svg`, mensagem “Guia inicial GCP”; SHA-256 `19c98485673fbbbbd49d58cafae07f770e93ab8082d76446f09e028c51844cb1`. Orienta Gmail cadastrado, projeto/quota project e AGY_ADC_AUTH=true. Não foi localizado script adicional; não inventar download/comando. Reutilizar setup e identidade da publicação anterior; executar etapa faltante do guia. Login/MFA é do participante. Um setup adicional que altere IAM/faturamento exige o responsável.

Os comandos seguintes são Bash, na raiz da cópia aprovada. Confirmar que ela contém o código golden, scripts/testes/docs; não usar checkout antigo. Não transferir .venv, .env, credenciais, extratos ou logs. Não presumir remote/commit: o workspace Windows ainda não tinha commit inicial.

```bash
export PINGO_PROJECT='batalha-time-08-g7ha'
export PINGO_REGION='us-central1'
export PINGO_SERVICE='pingo-backend'
export CLOUDSDK_CORE_PROJECT="$PINGO_PROJECT"
export GOOGLE_CLOUD_PROJECT="$PINGO_PROJECT"
export AGY_ADC_AUTH=true
gcloud auth list --filter=status:ACTIVE --format='value(account)'
gcloud projects describe "$PINGO_PROJECT" --format='value(projectId,lifecycleState)'
gcloud auth application-default set-quota-project "$PINGO_PROJECT"
```

O projeto precisa ser o acima, ACTIVE, com a mesma identidade autorizada. Se ADC estiver ausente, o participante executa `gcloud auth application-default login`; não ler o arquivo de credenciais, imprimir token ou criar chave JSON. Quota project não concede IAM. A preparação da venv, se necessária, é local e reversível:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
mkdir -p work
umask 077
python - <<'PY'
import google.auth
from google.auth.transport.requests import Request
try:
    credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    credentials.refresh(Request())
    assert credentials.valid
    print({'adc': 'PASS'})
except Exception as exc:
    print({'adc': 'FAIL', 'error_type': type(exc).__name__})
    raise SystemExit(1)
PY
```

Não executar passos dependentes após falha. Não contornar TLS. Auth gcloud e ADC devem funcionar; um token no Studio não verifica o backend.

## 3. Recursos existentes e estado para rollback

Inspecionar APIs existentes: run.googleapis.com, cloudbuild.googleapis.com, artifactregistry.googleapis.com, aiplatform.googleapis.com, bigquery.googleapis.com e logging.googleapis.com; Model Armor somente se permitido. Reutilizar repositório `agentes` e conta runtime `squad-agent-sa@batalha-time-08-g7ha.iam.gserviceaccount.com`. Não habilitar serviços nem criar recursos automaticamente para contornar erro.

```bash
gcloud services list --enabled --project="$PINGO_PROJECT" --format='value(config.name)'
gcloud artifacts repositories describe agentes --project="$PINGO_PROJECT" --location="$PINGO_REGION" --format='value(format,location)'
gcloud run services describe "$PINGO_SERVICE" --project="$PINGO_PROJECT" --region="$PINGO_REGION" --format=json > work/service-before.json
gcloud run services get-iam-policy "$PINGO_SERVICE" --project="$PINGO_PROJECT" --region="$PINGO_REGION" --format=json > work/service-iam-before.json
gcloud projects get-iam-policy "$PINGO_PROJECT" --format=json > work/project-iam-before.json
```

Inspecionar localmente sem expor envs. Confirmar conta runtime, revisão saudável, mapa de tráfego, secrets por referência, probe, privacidade, ausência de grants de invocação públicos/herdados e invoker IAM check habilitado. Não alterar IAM para corrigir. Se a configuração mudou desde a publicação anterior, preservar o estado atual verificado como rollback. Parar a publicação se não puder comprovar acesso privado. Não usar flags allow-unauthenticated/no-allow-unauthenticated/no-invoker-iam-check.

## 4. Golden real: configuração e consulta mínima

```bash
export DEMO_MODE=true
export DEMO_USER_ID='6491f4a4-67dc-49de-a38a-cf655ff77c33'
export DEMO_REFERENCE_DATE='2025-09-30'
export DATA_PROVIDER=bigquery
export AGENT_PROVIDER=gemini
export GEMINI_MODEL='gemini-3.8-flash'
export GOOGLE_CLOUD_LOCATION=global
export BIGQUERY_LOCATION=us-central1
export SAFETY_PROVIDER=local
```

Modelo/região acima foram registrados na publicação anterior; reconfirmar pelo backend. Não aceitar fallback OpenAI/Anthropic ou fixture. ID sintético é configuração do servidor, não segredo nem campo do frontend. Não passar persona_key/user_id arbitrário ao chat. `event_dataset_demo` continua enum legado de decision.data_mode; **runtime.data deve ser bigquery** e golden_analysis.data_source deve ser dataset_observed.

Executar o adapter real, preservando seu dry-run, parâmetros, timeout e teto de 1 GiB:

```bash
python - <<'PY'
import os
from datetime import date
from backend.data.bigquery_context import BigQueryContextProvider
try:
    context = BigQueryContextProvider(
        authorized_users={'persona-a': os.environ['DEMO_USER_ID']},
        reference_date=date.fromisoformat(os.environ['DEMO_REFERENCE_DATE']),
        golden_persona=True).get_context('persona-a')
    data = context.historical_summary['golden']
    assert data['origin'] == 'dataset_observed'
    assert data['reference_date'] == '2025-09-30'
    assert len(data['monthly']) == 6
    assert all(row['salary_cents'] == 675499 for row in data['monthly'])
    assert len(data['installments']) == 3
    assert sum(row['amount_cents'] for row in data['installments']) == 69078
    assert context.available_balance_cents is None
    print({'bigquery_golden': 'PASS', 'months': 6, 'installments': 3})
except Exception as exc:
    print({'bigquery_golden': 'FAIL', 'error_type': type(exc).__name__})
    raise SystemExit(1)
PY
```

A asserção confronta o dado consultado com o fornecido pelo usuário; ela não fabrica resultado. Se divergir, inspecionar apenas classificação/agregado indispensável. O SQL classifica salário por rótulo explícito normalizado `salario clt`; validar esse rótulo na tabela antes de generalizar. Não chamar toda entrada de salário, não inserir constantes no SQL nem usar fixture para passar. Flexíveis reais permanecem null porque a regra não foi fornecida. Detalhes em GOLDEN_PERSONA.md/BIGQUERY_HANDOFF.md. Não repetir exploração ampla nem enviar extrato ao LLM.

## 5. Gemini real pelo backend e safety

Em um terminal, com o ambiente acima e ADC saudável:

```bash
HOST=127.0.0.1 PORT=18081 python -m backend
```

Em outro terminal, na mesma venv e raiz:

```bash
python -m scripts.smoke_golden --base-url http://127.0.0.1:18081 --expect-agent gemini --expect-data bigquery
```

Aguardar health com prazo limitado antes do smoke. Somente PASS com runtime/modelo/origem corretos valida a integração golden: oito turnos, recálculos, primeira cobrança, saldo desconhecido, Supervisor opt-in, evento simulado e replay. Encerrar somente o processo temporário criado. Qualquer falha Gemini/BigQuery continua explícita; não alterar expectativas para demo.

Safety local está implementado e testado. Estado anterior de Model Armor: criação de template negada com 403. Consultar MODEL_ARMOR_HANDOFF.md; somente testar/reutilizar template/região já permitidos, sem IAM. Se permitido, validar input/output remoto em INSPECT_ONLY antes de escolher bloqueio. Se continuar bloqueado, manter SAFETY_PROVIDER=local explicitamente e registrar Armor BLOQUEADO, sem alegar integração remota. Não ampliar escopo para resolver IAM. Se o serviço atual já usa Armor validado, preservar essa configuração em vez de substituí-la por local.

## 6. Testes e build da imagem

```bash
python -m pytest -q
python -m pip check
python -m scripts.evaluate
python -m scripts.evaluate_golden
```

Esperado nesta revisão: 147 testes, 18 + 23 evals. Somente continuar com todos aprovados. Correções concretas de integração exigem repetir testes relevantes e suíte final. Nunca reduzir assertions financeiras para encaixar dado incorreto.

Dockerfile mantém HOST=0.0.0.0, PORT=8080 default substituído pelo Cloud Run, usuário sem privilégios e /health. Allowlists incluem `backend/data/golden_context.sql`; excluem fixture golden, frontend, testes, docs, .env e credenciais. Não embutir ADC/secrets na imagem. Secret Manager só se um mecanismo já autorizado exigir; Vertex/BigQuery usam identidade Google.

Reutilizar a conta e staging da build anterior `ae8047cc-ac61-4b9f-b00f-11549aa69441`. Consultar a build na região em que foi registrada (tentar us-central1; somente em NOT_FOUND consultar global), salvar `work/build-before.json`. Em PERMISSION_DENIED parar; não mudar IAM. Exemplo de leitura:

```bash
gcloud builds describe ae8047cc-ac61-4b9f-b00f-11549aa69441 --project="$PINGO_PROJECT" --region=us-central1 --format=json > work/build-before.json
```

Definir PINGO_BUILD_REGION com a região confirmada, PINGO_BUILD_SA com serviceAccount existente (nome completo projects/.../serviceAccounts/...) e PINGO_STAGING com `gs://<bucket existente de source.storageSource.bucket>/source`. Confirmar existência e autorização; não inventar/criar bucket ou conta. Gerar configuração mínima usando a conta existente e logs Cloud Logging, caso esse destino esteja permitido nessa conta:

```bash
export PINGO_IMAGE="us-central1-docker.pkg.dev/$PINGO_PROJECT/agentes/pingo-backend:golden-$(date -u +%Y%m%d%H%M%S)"
python - <<'PY'
import json, os
from pathlib import Path
config = {
    'steps': [{'name': 'gcr.io/cloud-builders/docker',
               'args': ['build', '-t', os.environ['PINGO_IMAGE'], '.']}],
    'images': [os.environ['PINGO_IMAGE']],
    'serviceAccount': os.environ['PINGO_BUILD_SA'],
    'options': {'logging': 'CLOUD_LOGGING_ONLY'},
}
Path('work/cloudbuild-golden.json').write_text(json.dumps(config), encoding='utf-8')
PY
gcloud builds submit . --project="$PINGO_PROJECT" --region="$PINGO_BUILD_REGION" \
  --config=work/cloudbuild-golden.json --ignore-file=.gcloudignore \
  --gcs-source-staging-dir="$PINGO_STAGING" --format=json > work/build-golden.json
```

Confirmar status SUCCESS; registrar ID/digest retornado. Se a conta não puder gravar Cloud Logging, reutilizar destino de logs previamente aprovado, sem grants/criação automática. O arquivo JSON de configuração é consumido pela CLI; não precisa ampliar allowlist do código enviado. Este roteiro usa [Cloud Build](https://docs.cloud.google.com/sdk/gcloud/reference/builds/submit) e a imagem resultante; não refaz build no deploy.

Com Docker disponível no ambiente de continuação, autenticar o credential helper existente se necessário (`gcloud auth configure-docker us-central1-docker.pkg.dev`), puxar a imagem e testar:

```bash
docker pull "$PINGO_IMAGE"
docker run --rm --entrypoint python "$PINGO_IMAGE" -c "from pathlib import Path; import backend.core.golden; assert Path('/app/backend/data/golden_context.sql').is_file(); assert not Path('/app/tests/fixtures/golden_persona.json').exists(); print('golden package PASS')"
docker run --detach --rm --name pingo-golden-image-smoke --publish 127.0.0.1:18082:8080 \
  --env HOST=0.0.0.0 --env PORT=8080 --env DEMO_MODE=true --env AGENT_PROVIDER=demo \
  --env SAFETY_PROVIDER=local "$PINGO_IMAGE"
```

Esse smoke de imagem usa a fixture **legada própria**, permitida para testar o processo; não a fixture golden excluída. Aguardar health por até 60 segundos e executar:

```bash
python - <<'PY'
import time, urllib.request
for attempt in range(30):
    try:
        with urllib.request.urlopen('http://127.0.0.1:18082/health', timeout=2) as r:
            if r.status == 200:
                break
    except Exception:
        time.sleep(2)
else:
    raise SystemExit('container health FAIL')
PY
python -m scripts.smoke_backend --base-url http://127.0.0.1:18082 --chat --expect-agent demo --expect-data own_synthetic_demo
docker stop pingo-golden-image-smoke
```

Executar cada comando somente se o anterior passar; em falha encerrar somente esse container e manter FAIL. Não confundir esse smoke com validação Gemini/BigQuery; essa ocorreu na seção 5 e será repetida na imagem Cloud Run. Sem build/smoke, manter container PENDENTE.

## 7. Publicar candidata privada, sem trocar tráfego

Pré-condições: mesmo ambiente autorizado, snapshot de rollback, testes e integrações reais aprovados, imagem aprovada. Definir PINGO_IMAGE_DIGEST com `us-central1-docker.pkg.dev/.../pingo-backend@sha256:...` obtido da build, não uma tag mutável. Confirmar que tag `golden` não pertence a outro trabalho; preservar tags/configuração existentes. Atualizar somente vars golden necessárias, preservando limites, ingress, identidade, secrets e safety atuais:

```bash
gcloud run deploy "$PINGO_SERVICE" --project="$PINGO_PROJECT" --region="$PINGO_REGION" \
  --image="$PINGO_IMAGE_DIGEST" --no-traffic --tag=golden \
  --update-env-vars="HOST=0.0.0.0,DEMO_MODE=true,DEMO_USER_ID=6491f4a4-67dc-49de-a38a-cf655ff77c33,DEMO_REFERENCE_DATE=2025-09-30,DATA_PROVIDER=bigquery,AGENT_PROVIDER=gemini,GOOGLE_CLOUD_PROJECT=batalha-time-08-g7ha,GOOGLE_CLOUD_LOCATION=global,BIGQUERY_LOCATION=us-central1,GEMINI_MODEL=gemini-3.8-flash" \
  --port=8080 \
  --startup-probe=httpGet.path=/health,httpGet.port=8080,periodSeconds=5,timeoutSeconds=3,failureThreshold=24 \
  --quiet
gcloud run services describe "$PINGO_SERVICE" --project="$PINGO_PROJECT" --region="$PINGO_REGION" --format=json > work/service-candidate.json
```

PORT é injetado pelo Cloud Run; não usar env PORT/GOOGLE_APPLICATION_CREDENTIALS. A conta runtime existente precisa continuar a aprovada. Conferir diff de configuração e a probe efetiva; Docker HEALTHCHECK não configura a probe Cloud Run. [Comando oficial de deploy](https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy).

Ler de `work/service-candidate.json` a URL e revisão da entrada `status.traffic` cuja tag é golden. Exportar PINGO_RUN_URL e PINGO_CANDIDATE_REVISION exatamente desses campos; não presumir latest nem construir URL. Aguardar revisão Ready e conferir ausência de tráfego principal para ela.

## 8. Smoke autenticado diretamente na URL real

Salvar o bloco Python abaixo como `work/smoke_golden_cloud.py`. Executar da raiz com `python work/smoke_golden_cloud.py` e PINGO_RUN_URL da candidata. O token permanece apenas em memória, sem log/arquivo; não usar set -x. O script exige health anônimo negado e usa o mesmo harness golden completo. O serviço deve estar no projeto/região já verificados.

```python
import json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import requests
sys.path.insert(0, str(Path.cwd()))
from scripts.smoke_golden import run_journey

base = os.environ['PINGO_RUN_URL'].rstrip('/')
url = urlsplit(base)
assert url.scheme == 'https' and url.hostname and url.hostname.endswith('.run.app')
assert not (url.username or url.password or url.path or url.query or url.fragment)
assert os.environ['PINGO_PROJECT'] == 'batalha-time-08-g7ha'
records = []
result = 'FAIL'
try:
    anon = requests.get(base + '/health', timeout=120, allow_redirects=False)
    records.append({'endpoint': '/health', 'authenticated': False, 'status': anon.status_code})
    assert anon.status_code in (401, 403)
    token = subprocess.run(['gcloud', 'auth', 'print-identity-token',
                            '--project=' + os.environ['PINGO_PROJECT']],
                           capture_output=True, text=True, timeout=30)
    assert token.returncode == 0 and token.stdout.strip()
    with requests.Session() as client:
        client.headers['Authorization'] = 'Bearer ' + token.stdout.strip()
        del token
        def request(path, body=None, *, raw=False):
            started = time.monotonic()
            response = client.request('GET' if body is None else 'POST', base + path,
                                      json=body, timeout=120, allow_redirects=False)
            records.append({'endpoint': path, 'authenticated': True,
                            'status': response.status_code,
                            'request_id': response.headers.get('X-Request-ID'),
                            'duration_ms': round((time.monotonic() - started) * 1000)})
            assert response.status_code == 200
            return response.content if raw else response.json()
        run_journey(request, expect_agent='gemini', expect_data='bigquery', observe=records.append)
    result = 'PASS'
except Exception as exc:
    records.append({'error_type': type(exc).__name__})
evidence = {'url': base, 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'result': result, 'checks': records}
Path('work').mkdir(exist_ok=True)
name = 'golden-cloud-smoke-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json'
Path('work', name).write_text(json.dumps(evidence, indent=2), encoding='utf-8')
print(json.dumps(evidence))
raise SystemExit(0 if result == 'PASS' else 1)
```

Somente PASS prova a jornada dessa URL. A seleção do modelo pode variar entre chamadas; se falhar não esconder o erro com stub. O harness exige salário/margens/parcelas fornecidos e recálculo correto. Captura somente metadados, não mensagens, identidade sintética ou extrato. Não sobrescreve o smoke anterior. Proxy localhost pode ajudar a diagnosticar, mas não substitui este aceite HTTPS.

## 9. Tráfego, logs e rollback

Após PASS da candidata, confirmar que tráfego/configuração não mudaram por outro responsável desde o snapshot. Publicar a revisão explicitamente testada e obter a URL principal real:

```bash
gcloud run services update-traffic "$PINGO_SERVICE" --project="$PINGO_PROJECT" --region="$PINGO_REGION" \
  --to-revisions="$PINGO_CANDIDATE_REVISION=100"
export PINGO_RUN_URL="$(gcloud run services describe "$PINGO_SERVICE" --project="$PINGO_PROJECT" --region="$PINGO_REGION" --format='value(status.url)')"
python work/smoke_golden_cloud.py
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$PINGO_SERVICE" \
  --project="$PINGO_PROJECT" --limit=30 \
  --format='table(timestamp,severity,jsonPayload.event,jsonPayload.status,jsonPayload.duration_ms)'
```

Registrar URL, revisão/tráfego, build/digest, timestamp, HTTP/request IDs, modelo/providers, testes, safety e limitações no STATUS-CORE. Verificar em Monitoring latência, 5xx, startup e memória; sem criar notificações. Não logar tokens, prompts, extrato, IDs de cliente ou erro bruto Google.

Se falhar após promoção, restaurar o **mapa de tráfego previamente verificado**. Apenas se ele era 100% `pingo-backend-00001-l22`, usar essa revisão com 100%; se havia split, restaurar exatamente o split. Comando: `gcloud run services update-traffic "$PINGO_SERVICE" --project="$PINGO_PROJECT" --region="$PINGO_REGION" --to-revisions='<MAPA_ANTERIOR_VERIFICADO>'`. Repetir health/smoke compatível com a versão anterior, sem golden. Não apagar serviço/revisões/imagens. [Rollback oficial](https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration).

## 10. Proibições e bloqueios

Não reescrever app/engine, mudar frontend/arquitetura, adicionar catálogo, offers, nova memória/banco, autenticação bancária, transação/push real ou múltiplos agentes. Não usar OpenAI/Anthropic no runtime. Não inferir saldo, crédito, renda futura ou agenda completa a partir do histórico. Sem SQL livre/identidade do modelo, fallback silencioso, segredos em código/logs ou chave JSON. Não mudar IAM/faturamento/acesso público nem contornar TLS/login/MFA.

**Indisponíveis no evento:** Pub/Sub, BigQuery Graph, Spanner, Security Command Center. RAG Engine, Feature Store, Model Garden e Agent Builder são opcionais e desnecessários nesta rodada. Cloud Storage só para staging de build já autorizado, sem componente novo do produto.

Bloqueio atual: leitura IAM ancestral `folders/900300571186:getIamPolicy` negada com 403; falta comprovar ausência de grants públicos herdados antes de build/publicação. ADC, SQL golden e jornada local real agora verificados; nova revisão ainda não publicada. Model Armor remoto continua não validado e safety local foi preservada. Usar rótulos VERIFICADO, IMPLEMENTADO NÃO TESTADO, MOCK/DEMO, BLOQUEADO e PLANEJADO. Configurar variável não verifica integração. Ao concluir a publicação e seus testes, parar.

## Referências oficiais fornecidas pelo evento

| Serviço | Referência e papel |
|---|---|
| Agent Platform | [Documentação](https://cloud.google.com/products/gemini-enterprise-agent-platform); contexto, sem plataforma extra obrigatória. |
| Agent Builder | [Documentação](https://cloud.google.com/products/agent-builder); opcional. |
| Agents CLI / ADK | [Documentação](https://adk.dev/get-started/agents-cli/); agente dentro do backend. |
| Model Garden | [Documentação](https://cloud.google.com/model-garden); validação de modelo, opcional como componente. |
| RAG Engine | [Documentação](https://cloud.google.com/vertex-ai/docs/generative-ai/rag-overview); não necessário. |
| Model Armor | [Documentação](https://docs.cloud.google.com/model-armor); input/output safety. |
| Google Cloud CLI | [Documentação](https://cloud.google.com/sdk/gcloud); operações autorizadas. |
| Cloud Shell | [Documentação](https://cloud.google.com/shell/docs); continuação Google. |
| Feature Store | [Documentação](https://cloud.google.com/vertex-ai/docs/featurestore); não necessário. |
| Cloud Run | [Documentação](https://cloud.google.com/run/docs); backend privado. |
| Revisões/rollback | [Documentação](https://cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration); tráfego e recuperação. |
| Cloud Storage | [Documentação](https://cloud.google.com/storage/docs); somente se surgir necessidade real. |
| BigQuery | [Documentação](https://cloud.google.com/bigquery/docs/introduction); histórico agregado readonly. |
| Cloud Logging | [Documentação](https://cloud.google.com/logging/docs); logs sanitizados. |
| Cloud Monitoring | [Documentação](https://cloud.google.com/monitoring/docs); latência/erros/recursos. |
| Secret Manager | [Documentação](https://cloud.google.com/secret-manager/docs/overview); somente se necessário ao mecanismo autorizado. |
| Cloud Build | [Documentação](https://cloud.google.com/build/docs); build no projeto. |
| Artifact Registry | [Documentação](https://cloud.google.com/artifact-registry/docs); repo existente/aprovado. |
| Hackathon | [Contexto, missão, avaliação e cronograma](https://live.popcast.com.br/itau/batalha_agentes/); ver WORKSHOP_REQUIREMENTS. |

# PROMPT PARA ANTIGRAVITY 2.0 / CLI

Continue em C:\Users\Eliane Gardim\Documents\Pingo ou na cópia aprovada no ambiente GCP já autorizado. Leia docs/STATUS-CORE.md, docs/GOLDEN_PERSONA.md e docs/ANTIGRAVITY_HANDOFF.md e execute esse roteiro para publicar a nova revisão golden do serviço pingo-backend, projeto batalha-time-08-g7ha, us-central1. Não reescreva o app nem altere frontend/arquitetura/IAM/faturamento.

Use DEMO_MODE=true, DATA_PROVIDER=bigquery, AGENT_PROVIDER=gemini, DEMO_USER_ID=6491f4a4-67dc-49de-a38a-cf655ff77c33 e DEMO_REFERENCE_DATE=2025-09-30. Revalide setup/ADC, SQL golden real e Gemini pelo backend. Nunca substitua falha por fixture. Preserve safety explícito; não tente corrigir Model Armor via IAM.

Reexecute pytest (147), evals (18+23), build e smoke da imagem. Preserve a revisão/tráfego atuais; teste candidata privada sem tráfego usando a jornada scripts/smoke_golden.py e o smoke HTTPS autenticado do handoff. Só então promova e repita health/jornada na URL principal. Registre URL, revisão, build/digest, providers e evidências sanitizadas no STATUS-CORE. Se houver bloqueio, informe operação e ação necessária; não marque a golden publicada. Pare após concluir, sem novas melhorias.
