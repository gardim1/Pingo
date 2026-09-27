> Atualização v2: 01_ESPECIFICACAO.md e 00_COMECE_AQUI.md prevalecem. UCP/AP2/Jev fora do primeiro corte; modos de acompanhamento e colaboração estão especificados nos documentos v2.

# Segurança e avaliação do Pingo

**Política proposta do protótipo: pingo-demo-v1. Não é documento oficial/homologado do Itaú.** Incorporar regras fornecidas pelo evento e registrar sua fonte; não inventar posições institucionais.

## Três pontos de controle, um módulo
Entrada: validação de tamanho/formato, identificação de requests fora do escopo e tentativas de acesso indevido.
Ferramentas: identidade/allowlist, tipos, limites, query parametrizada, checagem de consentimento e de efeitos colaterais antes de executar.
Saída: schema, coerência com resultado financeiro, proveniência, ausência de segredos, nenhuma alegação não sustentada e tom adequado.
Não criar dois agentes grandes só para ter uma caixa 'entrada' e outra 'saída'. ADK oferece callbacks/plugins nesses pontos; Model Armor é opção gerenciada se o projeto já tiver o acesso e os templates necessários.

Não confundir filtro genérico com revisão financeira: Model Armor não valida por si só a aritmética, o orçamento da pessoa ou políticas internas que não foram configuradas.

## Resultados de controle
ALLOW: segue normalmente.
CLARIFY: pedido legítimo incompleto, faz pergunta específica.
LIMIT: mostra apenas o que os dados sustentam.
BLOCK: recusa somente a ação insegura e explica o caminho permitido.
ERROR: informa indisponibilidade, não transforma falha em resposta financeira inventada.

'Não consigo pagar minha fatura' é um pedido legítimo, não prompt malicioso. Não bloquear só por falar em dívida, juros ou sofrimento financeiro.
Nenhum texto bruto do modelo deve chegar ao cliente antes do controle de saída. Templates determinísticos seguros são preferíveis a repetir indefinidamente o modelo. Se houver uma tentativa de correção generativa, limitar a uma, revalidar e depois aplicar fallback.

## Exemplos de mensagens
Pedido de dados de outra pessoa: 'Não posso acessar informações de outra pessoa nesta sessão. Podemos analisar o perfil selecionado para esta demonstração.'
Informação faltante: 'Consigo comparar o valor das parcelas, mas falta confirmar os compromissos futuros para avaliar seu caixa.'
Falha temporária: 'Não consegui consultar seus dados agora. Não vou concluir se essa compra cabe; tente novamente ou revise as condições informadas.'
Não citar 'políticas do Itaú' como justificativa genérica se a regra específica não foi fornecida.

## Observabilidade mínima
Registrar request_id, trace_id, duração total, duração de consulta/modelo/ferramenta, modelo e versão de política, número de chamadas, uso de tokens retornado pela API, bytes processados da consulta se disponíveis, status de guardrails, estado final e erro classificado.
Não registrar prompt completo, extrato, identificadores bancários, tokens, headers de autenticação ou dados de cartão. Hash de identificador não torna automaticamente um dado anônimo.
Calcular custo estimado com tabela de preço datada/configurável; não hardcode de valores da transcrição. Falta de usage não significa custo zero. Latência p50/p95 só após amostra real; informar tamanho da amostra, não inventar benchmark.

## Avaliação
Arquivo evals/cases.json contém 30 casos planejados. Integrador/pessoas do time transformam os itens em testes.
- Engine: testes determinísticos e invariantes de centavos/datas.
- Agente: seleção de ferramentas, pergunta necessária, uso de evidências, abstinência de conclusões indevidas.
- Segurança: isolamento, ataques em mensagens/descrições, falhas de ferramentas, não vazamento e não ação sem consentimento.
- UI: estados reais, correção de parâmetros, histórico fora da janela visível, sincronização de respostas concorrentes e navegação por teclado.
- Integração: Gemini e BigQuery autorizados; fixtures separados e rotulados.

Baseline honesto: a mesma jornada sem contextualização ou sem comparação visual, usando a mesma informação disponível. Não demonstrar impacto comparando com um baseline deliberadamente quebrado.
Critérios técnicos da demo: todos os casos críticos determinísticos passam; registrar falhas restantes; nenhuma compra real; limites de inferência explícitos.
Métricas de usuário propostas: compreensão do compromisso, clareza percebida e decisão coerente com prioridade declarada. São hipóteses até um teste real. Não usar conversão de compra como métrica principal de bem-estar.

## Deploy (pessoa 4 prepara, integrador aprova)
Confirmar conta/projeto, permissões, região do dataset, Artifact Registry, Cloud Build e conta de execução. Não habilitar faturamento pessoal, criar chaves JSON, abrir IAM ou tornar público sem aprovação.
Dockerfile multi-stage se for nova base: compilar frontend, copiar estáticos para backend. Servidor escuta 0.0.0.0:$PORT. Excluir .env, credenciais, .venv, node_modules e extratos do contexto de build.
Dados da demo: aliases do backend para um subconjunto sintético autorizado. Não expor endpoint que recebe ID arbitrário de cliente ou SQL livre. Limitar tamanho/tempo/quantidade de chamadas e acesso a ferramentas.
Verificar /health e uma análise completa na URL final, não apenas 'deploy concluído'. Uma revisão anterior funcional deve permanecer disponível para rollback pelo fluxo aprovado.
Persistência local no container não é durável. Não usar SQLite local como promessa de plano permanente em Cloud Run. Demo na sessão e exportação consentida permanecem explicitamente limitadas.
