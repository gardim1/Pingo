# Requisitos do workshop e do evento — Pingo backend

Atualizado em 2026-09-26. **VERIFICADO: leitura das duas transcrições e das quatro abas do site do evento.** Este documento registra o que as fontes sustentam; não certifica acesso aos serviços, execução de código, conformidade institucional ou deploy.

## Fontes, cobertura e precedência

- **D1:** `C:\Users\Eliane Gardim\Downloads\Workshop ｜ Batalha de Agentes ｜ Dia 1.pt.vtt`, SHA-256 `0a3b8434f6598e07b80835e6c961cc0ebeee294ff30566c82b8fd3d7c86f6e13`.
- **D2:** `C:\Users\Eliane Gardim\Downloads\Workshop ｜ Batalha de Agentes ｜ Dia 2.pt.vtt`, SHA-256 `9a2a0d749922919458ff9b31b50fd974fbfa94615f9cb378ba41d66345a56682`.
- As legendas foram lidas integralmente em blocos cronológicos, após retirar tags WebVTT e repetições sobrepostas do reconhecimento automático: D1, 3.782 linhas de texto até `02:34:44.920`; D2, 1.733 linhas até `01:37:57.840`. No D2 a despedida é em torno de `01:11:17`; depois há somente duas falas isoladas, `01:11:29` e `01:37:57`. Não há conteúdo legendado intermediário para interpretar. Leitura integral da transcrição não equivale a revisão do áudio/vídeo. Nenhuma transcrição bruta foi adicionada ao Git.
- [Site oficial do evento](https://live.popcast.com.br/itau/batalha_agentes/), consultado em 2026-09-26. As abas **O Contexto**, **Missão & Desafio**, **Critérios de Avaliação** e **Dinâmica & Cronograma** foram abertas no navegador, incluindo o carrossel de princípios e FAQ. A extração HTML inicial não resolvia textos dinâmicos; a leitura final usou a página renderizada.
- [Regulamento vinculado no site, 11 páginas](https://live.popcast.com.br/itau/batalha_agentes/Regulamento_Batalha_Agentes_VF.pdf), consultado em 2026-09-26, com atenção ao quadro de critérios/entregáveis e às regras de dados e autoria.
- Fontes locais cruzadas: `AGENTS.md`, `docs/STATUS-CORE.md`, `docs/DEPLOY_HANDOFF.md`, diagnóstico `CONTEXTO.md`, `DADOS.md`, `STATUS.md`, `HISTORIAS_DOS_DADOS.md`; pacote v2 `00`, `01`, `02`, `03`, `04`, `06`, `07`, `09`, `10` e verificação do pacote.

Precedência nesta rodada: pedido atual e sua atualização de serviços/escopo backend; esclarecimentos mais recentes do workshop; especificação v2; diagnóstico histórico e handoffs anteriores. O workshop explica capacidades e recomendações, mas não concede automaticamente IAM, quota, custo, região ou disponibilidade no projeto. O pedido atual autoriza evolução local e preparação cloud; não autoriza alterar IAM/faturamento nem publicar dados privados.

Os timestamps abaixo referem-se ao início do trecho nas legendas, não à hora civil. O texto é predominantemente paráfrase: erros como “guardios”, “login” por Logging e “AGI” por `agy` não são tratados como nomes de API.

## CONFIRMADO NO WORKSHOP

| Tema | Evidência nas transcrições | Consequência para Pingo |
|---|---|---|
| Finalidade e ia.i | D1 `00:01:44–00:03:24`: experiência conversacional ia.i e construção de soluções úteis. `00:50:02–00:52:21`: gestão financeira contextual, funcional e compreensível; não competição de ataques. | Evoluir a jornada de compra planejada; não substituir ia.i nem transformar o protótipo em assistente genérico. |
| Responsible AI desde o início | D1 `00:18:09–00:19:41`: confiança, responsabilidade, justiça e segurança; `00:34:03–00:36:09`: agentes devem nascer responsáveis, úteis e funcionar para diferentes contextos sociais. | Segurança e explicação fazem parte da funcionalidade. Evitar julgamento moral e inferências pessoais desnecessárias. |
| Memória e consentimento | D1 `00:10:18–00:10:29`: exemplo de memória sem consentimento é reprovado. D2 `00:26:34–00:27:04`: memória de longo prazo e sessões aparecem como aspectos distintos de gerenciamento. | Acompanhamento começa desligado. Sessão, dados de origem, plano consentido e memória longa são conceitos diferentes. O mecanismo `enabled=false/true` é decisão do produto, não API ditada pelo workshop. |
| Guardrail de entrada | D1 `00:24:49–00:25:08` e `00:31:09–00:32:20`: analisar a pergunta e deter conteúdo nocivo antes do modelo. | Inspecionar entrada antes de Gemini e de ferramentas; recusar tentativa insegura sem expor segredos ou outros clientes. |
| Guardrail de saída | D1 `00:25:08–00:25:23`, `00:31:59–00:32:20`: filtro após o modelo e antes do cliente para vieses/vazamentos. | Validar texto e números contra o engine antes da resposta HTTP. Não disponibilizar streaming de texto ainda não verificado. |
| Prompt injection e jailbreak | D1 `00:27:03–00:29:41`: ofuscação, apelo emocional, pretexto de pesquisa/teste, troca de persona e código; `00:34:50–00:35:14`: mitigar prompt injection e reprodução de vieses. | Evals devem incluir ataques variados. Instruções em dados/descrições não podem alterar autorização, tools ou identidade. |
| Falso positivo / escopo | D1 `00:23:21–00:24:00`, `00:44:05–00:44:34`: bloquear só o problemático, deixando o agente útil. | Pergunta benigna fora de finanças merece resposta curta ou redirecionamento, não incidente de segurança automático. |
| Viés e marca | D1 `00:20:02–00:21:28`: vieses podem vir do treinamento. `00:25:42–00:26:42` e `00:42:09–00:45:27`: exemplo “mulher pode ser CEO”; não fechar escopo a ponto de impedir posição respeitosa. | Responder que gênero não define capacidade de liderança. Não inventar declaração institucional; fontes oficiais são necessárias para atribuir posição ao Itaú. |
| Inferências sensíveis | D1 `00:29:45–00:30:48`, `00:34:24–00:34:47`: não deduzir procedimento médico, religião ou posição política a partir de transações sem necessidade válida. | Contexto mínimo financeiro; não construir perfil de saúde, religião, política, família ou profissão a partir do extrato. |
| Defesa em camadas e limites | D1 `00:32:58–00:33:11`: guardrails podem falhar. `00:37:32–00:38:28`: várias técnicas; não se exige fine-tuning em um fim de semana. | Controles locais de autorização/schema/cálculo continuam mesmo com filtro gerenciado. Não prometer proteção absoluta. |
| Gemini no runtime do evento | D1 `01:03:32–01:03:47`: acesso Gemini. D2 `00:16:43–00:17:43`: modelos terceiros não disponibilizados para o hackathon; `01:05:24–01:06:45` reforça Google e cita “3.8”. | Runtime Gemini configurável; falha explícita se não disponível. Sem fallback OpenAI/Anthropic. Nome oral não comprova ID API. |
| Código existente e ferramentas de desenvolvimento | D1 `01:05:13–01:07:23`, `01:08:35–01:09:15`: ferramentas externas/open source podem contribuir sob avaliação de riscos; solução avaliada no Google. `01:11:05–01:11:37`: permite adaptar motor existente. | Preservar o engine. Codex/Claude são ferramentas de desenvolvimento; não são providers do produto. |
| Agent Platform | D1 `00:57:25–00:58:16`; D2 `00:05:24–00:06:26`: plataforma para construção/gerenciamento de agentes, apresentada como evolução de Vertex AI. | Usar serviços necessários; nome de produto apresentado não exige migrar FastAPI para um novo runtime. |
| ADK | D2 `00:14:25–00:15:59`, `00:23:34–00:26:06`: kit de desenvolvimento por código, com Python e outras linguagens; disponibilidade anunciada. | ADK é opção preferencial de agent layer quando couber. Não obriga vários agentes nem invalida uso de SDK oficial com tools controladas. |
| BigQuery | D2 `00:36:07–00:36:15`: conexão BQ para o hackathon. `00:53:52–00:57:14`: warehouse analítico, consultas e assistente de dados; consumir agente também consome orçamento. | Adaptador de leitura com pré-agregação, query fixa e parâmetros. A demonstração do assistente SQL do console não autoriza o runtime a executar SQL gerado livremente. |
| Cloud Run | D2 `00:37:39–00:39:40`: publicação de aplicação/agente, monitoramento, revisões, tráfego e rollback. | Backend preparado para container, `0.0.0.0:$PORT`, health e rollback documentado. Deploy depende de configuração/permissões reais. |
| Cloud Build | D2 `00:39:53–00:41:21`: build, artefatos, integração com repositório e gatilhos de publicação. | Build reproduzível e smoke test. CI automático completo é opcional no MVP. |
| Model Armor | D2 `00:42:00–00:49:07`: proteção de modelos, injeção/jailbreak, dados sensíveis, Responsible AI, logging, idioma e modos de inspeção/bloqueio. `00:49:02–00:49:07`: uso apresentado como opcional. | Avaliar permissão/região/custo/template, integrar input/output se possível. Manter interface de provider e handoff se bloquear. Verificar detalhes do SDK na documentação atual. |
| Logging / Monitoring | D2 `00:38:36–00:39:09`, `00:46:28–00:46:45`, `00:50:56–00:53:48`: logs, filtros, métricas e limites de acesso. | Medir duração, tools, safety e erro com correlação. Não ligar logging de prompts/respostas financeiros brutos só porque o console o permite. |
| Secret Manager | D2 `00:49:13–00:50:54`: centralizar segredos, referenciar em código e gerir rotação; apresentador evita abrir valores. | ADC/identidade no backend; usar Secret Manager só se houver segredo realmente necessário. Nenhum segredo no Git/frontend/log. |
| Antigravity | D1 `02:23:34–02:24:13`: Cloud Shell garantido, instalação local ainda em avaliação. D2 `01:03:23–01:05:43`: CLI `agy` no Cloud Shell, autenticação e integração com o projeto. | Ferramenta de desenvolvimento/handoff, fora do caminho crítico do runtime. Não instalar localmente para satisfazer uma caixa no diagrama. |
| MCP e A2A | D2 `00:28:37–00:32:11`: protocolos, registry e ferramentas; `00:30:31–00:30:50`: A2A provavelmente desnecessário no hackathon; `00:31:11–00:31:40`: MCP complementa APIs. | Tools locais tipadas bastam para um agente. Não adicionar serviços MCP/A2A sem necessidade real. |
| Avaliação / evals | D1 `00:21:39–00:23:17`: ciclo ataque/defesa; `00:38:46–00:39:00`: responsabilidade entra na avaliação; `01:47:05–01:47:55` e `02:05:20–02:05:44`: revisar código/testes. D2 `00:36:18–00:36:57`: experimentos e métricas; `01:08:34–01:08:53`: traces e OpenTelemetry como complemento. | Testes determinísticos e harness de segurança/fluxo, com esperado/observado/pass/fail; não substituir invariantes por nota de LLM. |
| FinOps | D1 `00:58:24–00:59:19`, `01:06:45–01:07:23`, `02:28:23–02:29:36`: budget compartilhado e custo de desenvolvimento/runtime. D2 `00:12:02–00:12:48`, `00:57:24–00:58:53`: reforça orçamento por grupo. | Limitar chamadas, tokens, tempo, bytes e instâncias. Não presumir que budget interrompa gastos. Não alterar faturamento nem interpretar fala como saldo disponível. |

## INFERÊNCIA — decisões de implementação, não falas literais

1. **Um agente + tools + engine determinístico** é a menor arquitetura que atende ao foco da jornada e à defesa em camadas. O workshop mostra exemplos multiagente, mas não determina que Pingo deva ter vários agentes.
2. **Autorização antes de ferramentas** implementa os princípios de proteção: identidade imposta pelo backend, allowlist, Pydantic/schema, queries parametrizadas de leitura, timeout/bytes/linhas. O workshop não dita os nomes/classes nem esses valores de limite.
3. **Centavos, calendário, cenários e coerência numérica em código** traduzem confiança/segurança para o risco financeiro concreto. Não há fala autorizando LLM a calcular saldos ou juros.
4. **Consentimento separado de autenticação**, `enabled=false` inicialmente e eventos claramente simulados implementam a decisão atual de Pingo acompanha. Não há integração transacional real demonstrada pelas fontes.
5. **LocalSafetyProvider + ModelArmorSafetyProvider**, inspeção inicial e fallback explicitamente rotulado permitem desenvolvimento demonstrável sem esconder indisponibilidade. `INSPECT_ONLY` é escolha de rollout solicitada pelo usuário, não garantia de nome de enum do SDK.
6. **Logs mínimos e sem payload financeiro** conciliam observabilidade com minimização de dados. A fala sobre registrar comandos/respostas não é uma instrução para expor extratos ou segredos.
7. **Erro de provider não vira fixture**: preservar procedência e não mentir sobre integração; fixture só com demo explícita.
8. **Evals de perguntas difíceis legítimas e de falso positivo** são tão necessários quanto ataques: dívida e perguntas de igualdade devem continuar atendidas com respeito.

## OPCIONAL

- Model Armor é opcional na fala, mas a rodada atual exige **integração avaliada ou handoff preciso**. Guardrails locais continuam obrigatórios.
- ADK quando simplificar tools/callbacks; SDK oficial direto é alternativa do pedido atual com limite de dez minutos para tooling auxiliar.
- RAG Engine, Vector Search, Feature Store, Agent Builder/Studio, Agent Garden e memória longa são capacidades mostradas, não lista obrigatória do produto. Cloud Storage somente se surgir necessidade concreta.
- MCP/A2A, OpenTelemetry, experimentos no playground e CI com gatilhos podem complementar o MVP; testes/observabilidade mínimos independem deles.
- Um segundo agente somente com benefício real e testável documentado; nenhum é exigido pelas transcrições.

## NÃO NECESSÁRIO PARA O MVP

- Fine-tuning/treinamento de modelos, GPUs, rede de microagentes, banco complexo de memória, RAG amplo e reconstrução do projeto.
- UCP/AP2, checkout/pagamento, movimentação financeira, empréstimo/renegociação, notificações reais, integração bancária Itaú, scraping comercial ou aplicativo mobile. São excluídos pelo pedido atual; UCP/AP2 não apareceram como requisito nestas legendas.
- Gemini Enterprise corporativo: D2 `00:32:18–00:32:39` diz que não estaria disponível no evento. Não confundir com Agent Platform/Gemini disponibilizados.
- Explain Log por Gemini: D2 `00:52:56–00:53:48` o exclui do evento. Usar logs normais.
- **PROIBIDOS pela atualização atual do evento:** Cloud Pub/Sub, BigQuery Graph, Cloud Spanner e Security Command Center. Não criar dependência nem fallback para esses serviços, mesmo que Pub/Sub, Graph e SCC apareçam no overview de D2.

## Site e regulamento — confirmação complementar

O site prioriza uma jornada financeira específica, impacto demonstrável, acessibilidade, explicação e linguagem sem julgamento. Foram lidas as quatro abas e os cinco itens do carrossel. Para o backend, os critérios relevantes são uso de IA, contexto/memória/integrações e segurança/dados/experimentação. A dinâmica exige demonstração consistente com a arquitetura; o pitch tem cinco minutos. Agenda publicada: 26/09, 08h–18h; 27/09, 09h–13h, apresentações 09h30–12h. A data da página não altera a cobertura histórica da base. [Fonte: site do evento](https://live.popcast.com.br/itau/batalha_agentes/).

O regulamento explicita pesos: negócio 30%, experiência 20%, arquitetura/engenharia/dados 50%. Os cinco entregáveis incluem proposta de negócio, protótipo, racional de experiência, desenho de solução e explicação arquitetural. Código de terceiros e informação sigilosa exigem atenção às regras do evento; esta leitura não é parecer jurídico. [Fonte: regulamento, páginas 2, 6 e 9](https://live.popcast.com.br/itau/batalha_agentes/Regulamento_Batalha_Agentes_VF.pdf).

## Diagnóstico real cruzado — histórico não é presente

Fonte: `docs/diagnostico/docs/DADOS.md`, com jobs e limites de consultas; os números abaixo são **evidência de rodada anterior documentada**, não novas consultas executadas nesta leitura.

- `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`, localização `us-central1`, 467.585 lançamentos, 1.000 usuários, janeiro–dezembro de 2025. `saldo_apos` preenchido não comprova saldo de setembro/2026.
- 29.847 lançamentos de 992 usuários têm campos históricos de parcela; não há confirmação de vigência, vencimentos futuros, saldo ou crédito. 8.615 grupos são candidatos de recorrência, não contratos confirmados.
- `tipo=E/S` distingue direção; todo `vlr` é positivo. Entrada não significa salário. Valores da origem são FLOAT e exigem conversão/arredondamento explícitos antes de uso monetário.
- Há `Pagamento de fatura`; somar fatura e compras pode duplicar impacto. Exclusão indiscriminada também é incorreta; sem vínculo confiável, declarar limite e trabalhar com compromissos confirmados.
- Saídas antes da primeira entrada observada e vales de fluxo iniciados artificialmente em zero não provam saldo negativo ou inadimplência. Não inferir saúde, crença, emprego ou comportamento da população brasileira dessa base sintética.

Consequência: adapter fornece fatos históricos, candidatos, origem, coverage e limitações. Simulações atuais dependem de dados confirmados/hipóteses rotuladas; saldo desconhecido continua `null`.

## Divergências e pendências sem invenção

| Item | O que foi observado | Resolução |
|---|---|---|
| Nome de modelo | D1 `01:46:31`, `01:49:06`; D2 `00:08:48`, `01:05:17`, `01:06:36–01:06:45` contêm “3.8 flash”, com outros números mal reconhecidos. | A transcrição não verifica endpoint. **Evidência posterior:** em 2026-09-26, o Studio do projeto respondeu `OK` à chamada mínima em `gemini-3.8-flash`, região de interface `global`; ver `GCP_PREFLIGHT.md`. Backend/ADC ainda precisam de teste independente. |
| Modelos terceiros | D1 fala de possibilidade; D2 `00:16:43–00:17:43` exclui explicitamente no evento. | D2 + pedido atual prevalecem: Gemini somente. |
| Pub/Sub, Graph, SCC | Apresentados como capacidades em D2 `00:34:28–00:35:43`, `00:54:30–00:54:59`, `01:00:45–01:03:15`. | Atualização explícita do usuário os proíbe; Spanner também proibido. |
| “BQ 100%” | D2 `01:01:07–01:01:22` fala de amplo acesso, enquanto atualização exclui Graph. | Não interpretar fala genérica como permissão efetiva; testar somente API/recursos necessários. |
| Budget | ASR registra `$000` em D2 `00:12:14`/`00:57:50`, depois “1000” em `00:58:02`/`00:58:50`; diagnóstico cita US$ 1.000 como guia ainda não validado. | Confirmar orçamento/cotas com organização sem alterar faturamento. Não usar como saldo, cota garantida ou autorização de gasto. |
| Datas | Site/regulamento indicam 26–27/09/2026. D1 refere labs até quinta-feira dia 24; D2 diz até amanhã. Não há data civil nos VTT. | Não inventar datas de gravação; usar D1/D2 + timestamps. Base continua 2025. |
| Demonstração ≠ produto real | D1 `00:55:04–00:55:37` não promete colocar solução em produção no banco. | Cloud Run de demo não é integração Itaú, autenticação bancária ou homologação. |
| Descrições técnicas orais | Há analogias imprecisas e promessas amplas em D2 sobre BQ, segurança, thresholds e modalidades. | Usar falas como requisitos/intenção; validar contrato de API, idiomas, região, enforcement e preços na documentação oficial e no projeto. |

## Matriz de aceite desta rodada

**Atualização final do usuário em 2026-09-26, após confirmação com os organizadores:** Cloud Run efetivamente implantado é obrigatório. É uma decisão posterior; não atribuí-la retroativamente às transcrições. “Deploy OU handoff” deixou de ser critério válido. Não ampliar features, frontend ou arquitetura.

| Requisito | Evidência que a implementação deve produzir |
|---|---|
| Planejar e revisar | HTTP decision/review preservados; cenário modificado recalcula pelo engine. |
| Gemini | Chamada real pelo BACKEND, com modelo/região registrados; Studio e transporte falso não satisfazem a integração. |
| Dados | Adapter parametrizado e testado; integração BQ rotulada conforme execução real. |
| Input / tool / output | Evals de injection, SQL, outro usuário, número contraditório, marca e pergunta legítima. |
| Acompanha | Opt-out executado com zero tools/modelo; opt-in + evento simulado rotulado; sem notificação real. |
| Observabilidade | Request/session id, durações, tools, safety/modelo/engine/erros, sem payload sensível. |
| Cloud — OBRIGATÓRIO | Backend implantado no Cloud Run, URL real registrada, GET /health 200 e fluxo Pingo real nessa URL. Até isso ocorrer: CLOUD RUN DEPLOYED = PENDENTE. |
| Handoff | Model Armor e Antigravity com setup de participante, comandos, recursos permitidos e bloqueios reais. Handoff não substitui deploy obrigatório. |

Esta matriz é **requisito**, não resultado de teste. Resultados executados pertencem a `docs/EVAL_REPORT.md`, `docs/STATUS-CORE.md` e ao preflight/handoff Google.
