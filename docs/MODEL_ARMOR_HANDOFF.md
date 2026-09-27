# Model Armor — integração e handoff

Atualizado em 2026-09-26. Projeto: `batalha-time-08-g7ha`. Região proposta: `us-central1`.

## Estado e evidência

- **VERIFICADO localmente:** `backend/safety/` implementa a interface `SafetyProvider`; `LocalSafetyProvider` aplica controles determinísticos e `ModelArmorSafetyProvider` acrescenta inspeção remota sem retirar os controles locais.
- **VERIFICADO localmente:** 40 testes de `tests/test_safety.py` passaram com `.\.venv\Scripts\python.exe -m pytest tests/test_safety.py -q`. Os testes de Model Armor substituem somente o transporte HTTP; são testes de adapter, **não evidência de chamada GCP real**.
- **IMPLEMENTADO NÃO TESTADO na nuvem:** uso de ADC, endpoint regional, input/output em português, timeout, interpretação de respostas e erro explícito. Nenhum template, API, papel IAM, acesso público ou recurso de faturamento foi criado nesta frente.
- **BLOQUEADO para afirmação de integração real:** falta validar autenticação, API, permissões e template no projeto. O status geral e eventual evidência posterior ficam em `STATUS-CORE.md`.

## Contrato de integração

```python
from backend.safety import (
    LocalSafetyProvider, ModelArmorSafetyProvider, OutputContext, SafetyAction,
)

# Escolha local é explícita, não recuperação silenciosa de falha do Google.
local = LocalSafetyProvider()
managed = ModelArmorSafetyProvider(
    "projects/batalha-time-08-g7ha/locations/us-central1/templates/pingo-safety",
    enforcement="INSPECT_ONLY", timeout_seconds=5,
)
input_verdict = managed.inspect_input("Quero planejar uma compra.")
# Só continuar se action == ALLOW. REDIRECT retorna safe_message;
# BLOCK interrompe; ERROR é indisponibilidade e deve virar erro HTTP explícito.

# O texto esperado deve vir de template do backend após o engine.
expected = "Posso comparar as condições informadas e mostrar os compromissos."
output_verdict = managed.inspect_output(expected, OutputContext(trusted_text=expected))
```

O provider retorna `action`, `reason`, `provider`, `safe_message` e códigos `findings`. Não inclui payload ou mensagem bruta de erro. Dependências remotas: `google-auth` e `requests`; o SDK `google-cloud-modelarmor` não é necessário neste adapter REST. Nenhum runtime OpenAI/Anthropic é usado.

O integrador deve inspecionar mensagens e campos livres que poderiam introduzir instruções (rótulo, finalidade, preferências), antes das ferramentas. A autorização de identidade, schemas, allowlist e SQL parametrizado continuam na camada de tools. `OutputContext.trusted_text` não pode vir do modelo, snapshot do cliente ou descrição bruta do dataset. Deve vir de texto controlado pelo servidor, com valores do engine. Uma comparação com o próprio texto livre do LLM não estabelece segurança. Saída sem proveniência é bloqueada mesmo quando não tem dígitos; regex não comprova verdade financeira nem ausência de viés.

## O que validar no Google, sem alterar permissões

No Cloud Shell, dentro da cópia do projeto:

```sh
gcloud auth list --filter=status:ACTIVE --format='value(account)'
gcloud config get-value project
gcloud projects describe batalha-time-08-g7ha --format='value(projectId,lifecycleState)'
gcloud services list --enabled --project=batalha-time-08-g7ha --filter='config.name:modelarmor.googleapis.com' --format='value(config.name)'
gcloud model-armor templates list --project=batalha-time-08-g7ha --location=us-central1
gcloud model-armor templates describe pingo-safety --project=batalha-time-08-g7ha --location=us-central1
gcloud beta quotas info list --project=batalha-time-08-g7ha --service=modelarmor.googleapis.com --format='table(metric,quotaInfos.dimensionsInfos.details.value)'
```

Ausência de template é diferente de 403. Registrar código e operação sem token. Não automatizar login/MFA nem ler arquivos de credencial. Em caso de autenticação ou permissão ausente, pedir ao responsável do evento a ação específica e continuar em modo local explicitamente rotulado.

O runtime necessita `modelarmor.templates.useToSanitizeUserPrompt` e `modelarmor.templates.useToSanitizeModelResponse`; leitura e criação têm permissões distintas. O administrador pode avaliar os papéis mínimos correspondentes. Este handoff não autoriza mudar IAM. [Referência de sanitização](https://docs.cloud.google.com/model-armor/sanitize-prompts-responses).

## Região, idioma, limites e custo

`us-central1` está na lista oficial de regiões. Não reutilizar automaticamente a localização de outro serviço. [Regiões](https://docs.cloud.google.com/model-armor/locations).

RAI e detecção de injection/jailbreak têm português entre os idiomas testados. O adapter envia `enableMultiLanguageDetection=true` e `sourceLanguage=pt`. Model Armor analisa chamadas isoladas, não mantém memória da conversa e não decodifica automaticamente ataques codificados. `INSPECT_ONLY` é indicado para observar falsos positivos, mas não protege sozinho; os controles locais permanecem bloqueantes. Em inspeção remota, consultar os registros apropriados para medir detecções, sem confundir recusa do Gemini com bloqueio do Armor. [Visão geral](https://docs.cloud.google.com/model-armor/overview).

Na consulta de 2026-09-26, a documentação informa 1.200 consultas/minuto por projeto e limites de 65.536 tokens para PI/RAI/CSAM e 130.000 para SDP. Quotas reais podem ser menores. Pingo limita cada texto desta camada a 24.000 caracteres e interrompe erro, inspeção parcial ou detector necessário ausente. Não toma `EXECUTION_SKIPPED` como aprovação. [Quotas](https://docs.cloud.google.com/model-armor/quotas), [semântica de resultados](https://docs.cloud.google.com/model-armor/reference/rest/v1/SanitizationResult).

O preço público consultado informa faixa gratuita de até 2 milhões de tokens/mês e US$ 0,10 por milhão adicional para Model Armor. Isso **não prova** crédito disponível nem custo zero no projeto do evento; consumo é compartilhado e inspecionar entrada e saída adiciona uso. Confirmar condições efetivas antes de habilitar recursos; não alterar faturamento. Security Command Center não é necessário e está proibido pelo evento. [Preço oficial](https://cloud.google.com/security/products/model-armor).

## Configuração mínima do template — executar somente com acesso autorizado

Primeiro reutilizar template adequado existente. Se faltar API, o responsável autorizado deve habilitar `modelarmor.googleapis.com`; o agente não deve contornar falta de permissão. Se criação estiver permitida e custo/configuração estiverem validados, usar este JSON como corpo de criação, sujeito à validação de compatibilidade do projeto:

```json
{
  "filterConfig": {
    "raiSettings": {
      "raiFilters": [
        {"filterType": "HATE_SPEECH", "confidenceLevel": "MEDIUM_AND_ABOVE"},
        {"filterType": "HARASSMENT", "confidenceLevel": "MEDIUM_AND_ABOVE"},
        {"filterType": "DANGEROUS", "confidenceLevel": "MEDIUM_AND_ABOVE"},
        {"filterType": "SEXUALLY_EXPLICIT", "confidenceLevel": "MEDIUM_AND_ABOVE"}
      ]
    },
    "piAndJailbreakFilterSettings": {"filterEnforcement": "ENABLED", "confidenceLevel": "MEDIUM_AND_ABOVE"},
    "sdpSettings": {"basicConfig": {"filterEnforcement": "ENABLED"}},
    "maliciousUriFilterSettings": {"filterEnforcement": "ENABLED"}
  },
  "templateMetadata": {
    "enforcementType": "INSPECT_ONLY",
    "multiLanguageDetection": {"enableMultiLanguageDetection": true}
  }
}
```

Salvar como `model-armor-template.json` fora dos arquivos de credenciais. Criar por `POST https://modelarmor.us-central1.rep.googleapis.com/v1/projects/batalha-time-08-g7ha/locations/us-central1/templates?templateId=pingo-safety`, com ADC e esse corpo. Não enviar token ao terminal. Exemplo executável no Cloud Shell, **após as verificações anteriores**:

```sh
python - <<'PY'
import json
import google.auth
from google.auth.transport.requests import AuthorizedSession
credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
session = AuthorizedSession(credentials)
with open('model-armor-template.json', encoding='utf-8') as source:
    body = json.load(source)
url = 'https://modelarmor.us-central1.rep.googleapis.com/v1/projects/batalha-time-08-g7ha/locations/us-central1/templates'
response = session.post(url, params={'templateId': 'pingo-safety'}, json=body, timeout=15)
print({'http_status': response.status_code, 'created': response.status_code in (200, 201)})
raise SystemExit(0 if response.status_code in (200, 201) else 1)
PY
```

Os campos seguem a [referência REST do template](https://docs.cloud.google.com/model-armor/reference/rest/v1/projects.locations.templates). A API regional de sanitização aceita `userPromptData.text` em `:sanitizeUserPrompt` e `modelResponseData.text` em `:sanitizeModelResponse`; o adapter já constrói essas chamadas. O modo configurado no aplicativo não altera o modo do template: conferir ambos. [Gerenciamento e enforcement](https://docs.cloud.google.com/model-armor/manage-templates).

## Smoke e passagem para bloqueio

Após criar/reutilizar o template, executar na raiz do projeto:

```sh
python - <<'PY'
from backend.safety import ModelArmorSafetyProvider, OutputContext
provider = ModelArmorSafetyProvider(
    'projects/batalha-time-08-g7ha/locations/us-central1/templates/pingo-safety',
    enforcement='INSPECT_ONLY',
)
text = 'Posso comparar as condições informadas para esta compra.'
for phase, result in [
    ('input', provider.inspect_input('Quero planejar uma compra de celular.')),
    ('output', provider.inspect_output(text, OutputContext(trusted_text=text))),
]:
    print({'phase': phase, 'provider': result.provider, 'action': result.action,
           'reason': result.reason, 'findings': result.findings})
PY
```

Confirmar `provider=model_armor`, ausência de ERROR e evidência das duas operações. Ataques que o filtro local bloqueia não chegam à nuvem por design; para avaliar especificamente detectores gerenciados, usar a API regional diretamente com conjunto sintético aprovado, nunca dados de cliente. Medir falsos positivos com dívida/fatura, planejamento e a pergunta “Uma mulher pode ser CEO?”. A resposta segura não atribui posição institucional ao Itaú.

Antes de ativar bloqueio, registrar amostra e resultados reais em `EVAL_REPORT.md`. Revisar o template para `INSPECT_AND_BLOCK` e configurar o aplicativo igualmente; reexecutar input e output. Sem evidência, manter rótulo **IMPLEMENTADO NÃO TESTADO** para integração real. Falha HTTP, timeout, credencial, schema inesperado, ausência de PI/RAI ou inspeção parcial retorna ERROR em ambos os modos, sem trocar para local.

## Logs, limites e rollback

Pingo deve registrar request/session IDs opacos, fase, provider, action, reason, duração e códigos de findings. Não registrar prompt, resposta financeira, extrato, token, corpo de erro ou achados SDP brutos. Avaliar configuração/retenção dos logs de plataforma antes de habilitá-los; usar apenas dados sintéticos na avaliação até comprovar minimização. O modo inspect-only precisa evidência nos logs gerenciados; não inferir sucesso de detecção só pela resposta textual.

Rollback: retornar ao template/revisão de configuração previamente validado. Se for preciso operar sem serviço gerenciado, selecionar `local` explicitamente e registrar a alteração como limitação; nunca transformar falha do Armor em sucesso local automaticamente. O rollback do serviço segue `ANTIGRAVITY_HANDOFF.md`.

Limites: regras locais não cobrem toda paráfrase, idioma, codificação ou contexto indireto; não são uma garantia contra todos os ataques. Proveniência de saída e autorização de tools constituem barreiras separadas. Não há memória longa, bloqueio de conta, notificação real ou incidente automático para simples pedido fora do escopo. Sem Cloud Pub/Sub, BigQuery Graph, Cloud Spanner ou Security Command Center.
