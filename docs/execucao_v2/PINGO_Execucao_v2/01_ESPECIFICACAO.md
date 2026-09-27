# Pingo — especificação proposta v2

## Intenção
A pessoa quer comprar um celular. Pingo mostra as consequências das condições disponíveis, respeita prioridades declaradas, permite ajustes e registra um plano revisável. Não é banco autônomo, motor de aprovação de crédito ou loja.

Fonte de direção: desenho, transcrições e refinamento do usuário. Dois modos: planejamento iniciado pelo cliente e acompanhamento consentido após uma compra. No MVP o segundo usa um evento explicitamente simulado na sessão, sem jobs, notificações externas ou acesso a compras bancárias reais.

## Escopo essencial
1. Escolher uma persona sintética autorizada para demonstração.
2. Informar uma compra e condições; o agente pede somente o dado essencial ausente.
3. Consultar dados relevantes no BigQuery, com consultas parametrizadas e controladas.
4. Simular uma ou duas alternativas sustentadas por dados/condições explícitas.
5. Exibir resumo, compromissos futuros, janela da projeção e evidências.
6. Alterar uma preferência/condição e recalcular.
7. Salvar resumo do plano por ação explícita e poder revisá-lo.
8. Demonstrar pelo menos um caso de informação insuficiente e um controle de segurança.

## Arquitetura mínima
Um serviço Cloud Run: React/TypeScript compilado, servido por Python/FastAPI. Um agente Gemini com ferramentas, não uma rede de microagentes. ADK é a opção preferencial quando facilitar callbacks e integração no ambiente autorizado; chamadas de funções diretas são aceitáveis se a equipe decidir. Não reescrever stack já iniciada sem bloqueio real.

Fluxo: requisição -> validação de entrada -> agente -> autorização/validação de cada ferramenta -> consulta/cálculo -> validação da resposta e política -> resposta à interface.
Guardrail de saída não substitui autorização prévia de ferramentas. Calcular e ler dados não autoriza gravar um plano, preparar um checkout ou efetuar compra.

Ferramentas de domínio propostas:
- get_financial_context: produz contexto normalizado, origem, janela e lacunas.
- simulate_options: aritmética e agenda de parcelas em código.
- get_evidence: retorna explicações estruturadas, sem extratos brutos.
Não dar SQL arbitrário ou ferramentas administrativas ao agente.

## Ambiente de referência
Projeto: batalha-time-08-g7ha.
Tabela informada: batalha-time-08-g7ha.hackathon_dados.extrato_sintetico.
Região de publicação do guia: us-central1; localização BigQuery deve ser descoberta separadamente.
Pipeline: Cloud Build -> Artifact Registry (agentes, sujeito a verificação) -> Cloud Run.
Modelo indicado no guia e citado na transcrição: gemini-3.8-flash. Confirmar acesso/endpoint da conta do evento antes da primeira chamada; não usar credencial pessoal como substituição silenciosa.
Conta de serviço de execução/ADC conforme o ambiente; não gerar chaves JSON. Secret Manager somente no backend, quando exigido pelo mecanismo autorizado.

O relatório HISTORIAS_DOS_DADOS.md recebido do usuário registra acesso e consultas: 467.585 lançamentos de 1.000 usuários nos 12 meses de 2025, us-central1. Este pacote não reexecutou os jobs e não contém o schema completo; pessoa 3 deve usar docs/DADOS.md e SQL da exploração existente. Há marcadores parcela_atual/parcela_total em eventos históricos, não um calendário futuro confiável. Não repetir descoberta ampla nem inventar campos ausentes.

## Contrato público e propriedade
Arquivo contracts/decision-response.schema.json define a proposta de resposta. Integrador aprova mudanças e informa frontend/dados/QA; ninguém muda o contrato unilateralmente.

Endpoints propostos:
- GET /health -> {"status":"ok"}; não expor configuração/segredos.
- GET /api/demo/personas -> [{"key":"persona-a","label":"Exemplo A"}]. Chaves públicas são aliases de uma allowlist aprovada no backend, não IDs arbitrários de clientes.
- POST /api/decision -> DecisionResponse.
- POST /api/decision/review -> DecisionResponse após nova consulta/cálculo.

Entrada de /api/decision:
- message: string, 1–2000 caracteres.
- persona_key: string, somente allowlist do backend.
- decision: objeto opcional {label, total_price_cents, upfront_cents, installment_count, first_due_date}.
- preferences: objeto opcional {purpose, can_wait, protected_items}; informações declaradas, não fatos bancários.
- previous_request_id: string opcional, correlação; não é credencial nem fonte financeira.
Valores monetários em inteiros de centavos não negativos; parcelas entre 1 e 60 neste MVP. Se preço, data ou condições estiverem incompletos, perguntar antes de calcular. Alterar total não mantém cronograma antigo.

Entrada de /api/decision/review:
Os mesmos campos, mais plan_snapshot: {decision, preferences, saved_as_of_date}.
Qualquer snapshot do cliente é não confiável: ignorar totais/calculados alegados; reconstruir contexto autorizado e recalcular. Para demo, event: {kind:"confirmed_obligation_ended", obligation_ref} é permitido somente se DEMO_MODE=true, em uma allowlist de fixtures próprios, sempre rotulado "evento simulado". Não presumir quitação pela simples passagem do tempo.

## Estado e persistência
MVP sem um novo banco: conversa/seleção/rascunho ficam na sessão do navegador; o backend reconsulta o contexto autorizado em cada análise. Não depender de memória local do processo Cloud Run para autorização ou continuidade.
Salvar plano = snapshot mínimo com os campos escolhidos, por consentimento. Manter na sessão; permitir baixar um JSON próprio. Persistência além da sessão e notificações reais estão fora do MVP. Não guardar extrato, token, CPF ou dados de sessão em localStorage.
Não afirmar que o plano sobreviverá ao encerramento da sessão sem um mecanismo persistente implementado. Uma demo de "revisitar" pode continuar na mesma sessão ou reabrir um snapshot mínimo consentido.

## Regras financeiras essenciais
- Separar movimento da conta, compras do cartão e liquidação de fatura; sem distinção confiável, reduzir a análise e informar a limitação.
- Entrada observada não é automaticamente renda recorrente.
- Sem saldo inicial confirmado, min_balance_cents=null e projection.mode="unavailable".
- Agenda de parcelas cobre todo o compromisso, mesmo quando o gráfico exibe só 30/60/90 dias.
- Não declarar viabilidade global usando uma janela parcial. Exibir remaining_after_window_cents.
- Custos alternativos, taxas, descontos e valor residual vêm de condições explícitas; não inventar benefícios de assinatura ou 'iPhone para Sempre'.
- Regra de comparação: mesmas datas/janela e premissas comuns, mostrando qualquer mudança.
- No mesmo dia, convenção conservadora: saídas antes de entradas quando a ordem intradiária for desconhecida; informar a convenção e não chamar isso de saldo bancário efetivo.
- Divisão em parcelas deve preservar todos os centavos; tratar final do mês e ano bissexto.
- Profissão ou 'é para trabalhar' não gera renda futura garantida. Renda adicional é hipótese declarada e exibida separadamente.
- Não inferir emprego, filhos, veículo ou obrigação de IPVA/13º a partir de descrições vagas.
- As_of_date depende do período realmente analisado. Histórico de 2025 não é posição atual em setembro/2026.

## UX proposta
Identidade Pingo: fundo claro, texto escuro, acento azul-petróleo, numerais tabulares e espaço em branco. Palavra 'Pingo' pode ter marca simples feita com tipografia; não gastar tempo com mascote antes da jornada.
Desktop: conversa compacta à esquerda, decisão visual à direita. Mobile: painel principal acima, conversa recolhível. Resposta financeira final aparece apenas depois de validação; carregamento pode informar 'consultando dados'/'calculando' sem expor raciocínio interno.
Telas/estados: intenção; falta uma informação; comparação; evidências; plano salvo/revisão; falha recuperável.
Elementos da comparação: total, entrada, parcelas completas, janela analisada, saldo mínimo somente se sustentado, compromisso fora da janela, premissas.
Botões: Ajustar condições; Ver o que foi considerado; Salvar meu plano; Rever meu plano.
Não mostrar 'Compra aprovada', 'renda garantida' ou porcentagem de confiança como probabilidade de segurança financeira.
Mensagem útil de incerteza: 'Consigo mostrar as parcelas. Para avaliar o dinheiro que restará, falta confirmar seu saldo e os próximos compromissos.'
Acessibilidade: teclado, foco visível, labels, contraste, alternativa textual/tabular para gráficos, movimento reduzido. Não alegar certificação sem auditoria.

## Critério de conclusão
Um fluxo UI -> Gemini autorizado -> ferramenta -> cálculo -> resposta validada funciona; uma alteração recalcula; um caso incompleto abstém corretamente; um caso de abuso não expõe dados; URL publicada somente com autorização e verificada em outro navegador; entregáveis distinguem fatos, mocks e hipóteses.

## Adendo v2 — dois modos, mesmo motor
**Quero planejar:** mantém `/api/decision` e `/api/decision/review` e o contrato v1 de saída. O chat consulta, pede confirmação contextual quando necessário, compara e salva um plano. A meta é ajudar a realizar objetivos, sem prometer viabilidade que os dados não sustentam.

**Pingo acompanha:** inicialmente DESLIGADO. Toggle claro: “Revisar minhas próximas decisões nesta demonstração”. A pessoa pode desligar a qualquer momento. Não o chamar de supervisor, não executar cobranças, cancelamentos, renegociações ou empréstimos. Na demo, botão “Simular compra realizada” cria evento de fixture e a tela mostra `EVENTO SIMULADO — não é uma transação bancária`.

Endpoint adicional `POST /api/accompaniment/review`: recebe persona_key da allowlist, consent_enabled boolean, event={event_id, kind:"demo_purchase_posted", offer_ref} e condições confirmadas da sessão segundo o contrato do integrador. offer_ref deve existir na allowlist de fixtures no servidor; rejeitar evento não permitido ou DEMO_MODE=false. consent_enabled=false retorna `reviewed:false, reason:"opted_out", decision:null` ANTES de chamar BigQuery, Gemini ou cálculo. Consentimento não substitui autenticação/escopo por cliente.

Com consentimento, o backend calcula o efeito do compromisso uma vez, sem deduzir o preço inteiro além das parcelas. Reaproveita o motor de cenários e retorna `{reviewed:true, reason:"reviewed", decision:DecisionResponse}` ou reason="needs_confirmation" com decisão que pergunta o essencial. Interface mostra um card não modal com revisão; suprime exibição repetida do mesmo event_id nesta sessão. Não há garantia de processamento exactly-once ou acompanhamento entre dispositivos. É uma revisão demonstrativa disparada por evento, não monitoramento de produção.

Preferências/snapshot da demo continuam na sessão do navegador, como no v1, e são revalidados pelo backend. Não coletar histórico de compras quando modo estiver desligado. Sem banco persistente aprovado, não prometer que consentimento ou plano sobrevivem ao fim da sessão. Persistência durável, webhook real e jobs são integração futura.

Mensagem proposta: “Essa compra mudou os compromissos que você informou. Vamos comparar alternativas para os próximos pagamentos?” Somente dizer que há saldo projetado abaixo de uma margem se cálculo e premissas sustentarem; nunca inferir culpa, irresponsabilidade ou inadimplência.

## Adendo v2 — entrada financeira complementar
Adicionar ao request comum `confirmed_context` opcional, validado no backend: `{as_of_date, available_balance_cents, scheduled_cashflows:[{ref,date,amount_cents,direction}], protected_buffer_cents}`. Datas ISO; centavos inteiros; direction somente inflow/outflow; saldo não nulo pode ser negativo, margem não negativa e demais valores não negativos. Cada registro deste objeto é `user_confirmed` (ou `own_synthetic_fixture` em fixtures próprias), nunca `dataset_observed`.

Não aceitar um saldo calculado pelo navegador como resultado: recomputar tudo no servidor. confirmed_context complementa a base, não afirma que o histórico de 2025 está atualizado. Para repetição de compromissos confirmados usar refs distintas por vencimento; rejeitar ref duplicada. Metas, prioridades e purpose são declarações, não profissão/renda inferida. Os três campos essenciais ausentes podem ser perguntados em uma pergunta curta agrupada; não criar um onboarding enorme.

## Adendo v2 — marca e recomendações
Posicionamento da instituição só a partir de trecho oficial disponibilizado, com URL/data/versão e revisão do responsável. Sem evidência, não falar “o Itaú pensa X”. Uma pergunta benigna como “Uma mulher pode ser CEO?” pode receber uma frase respeitosa e correta, seguida de retorno ao escopo; não é prompt injection por ser fora do tema.

Instrução de programar algo sem relação com finanças: redirecionamento educado, não rótulo de ataque. Tentativa de extrair segredos/dados de outros clientes: bloquear e não executar ferramentas. Output guardrail valida inclusive alucinações financeiras, discriminação, atribuições institucionais sem fonte e tom culpabilizante.

Produtos Itaú podem aparecer se pertinentes, mas não priorizar comissão/conversão em detrimento do cliente. A página oficial do iPhone pra Sempre contém pagamento final de até 30% além das 21 parcelas; sem condições completas verificadas, oferecer apenas informação/link contextual, nunca uma comparação que esconda esse compromisso. Não implementar busca comercial em tempo real nesta etapa.
