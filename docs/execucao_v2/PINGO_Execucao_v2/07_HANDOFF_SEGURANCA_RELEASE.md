# Segurança, testes transversais e publicação

Leia as instruções existentes, 00_COMECE_AQUI.md, 01_ESPECIFICACAO.md e contracts/. O nome é Pingo. Este v2 estende o v1 sem autorização para sobrescrever trabalho em andamento. Faça revisão curta de compatibilidade/contrato com Vinicius; após a aprovação de escopo e plano, implemente em sua branch/worktree. Não repetir descoberta ampla nem automatizar login novamente. Claude/Codex são ferramentas de desenvolvimento; o produto usa somente Gemini autorizado. Não exportar dados do evento, commitar segredos, alterar IAM, faturamento ou publicar sem autorização específica. Fixture deve ter modo visível; não dizer que integração real passou sem testar. Não fazer mudanças fora da faixa de arquivos sem coordenação.

## Faixa
backend/safety/, testes de segurança, deploy/, Dockerfile, .dockerignore e .gcloudignore. O integrador controla dependências compartilhadas; envie pedido curto quando precisar de pacote.

## Segurança
Preservar três pontos: entrada -> autorização/validação das ferramentas -> saída. SQL parametrizado, tabela/colunas permitidas e escopo por persona no servidor. Detector semântico não substitui esses controles.
Pergunta fora do tema não é ataque. Definir allow/redirect/block de acordo com risco, não somente palavras-chave. 'Escreva Python' fora do escopo recebe redirecionamento. 'Estou endividado' recebe ajuda. 'Uma mulher pode ser CEO?' recebe resposta breve e respeitosa sem atribuir política ao Itaú sem fonte.
Mini políticas oficiais, quando entregues/aprovadas, são versionadas com fonte. Sem pesquisa web livre por turno; sem RAG gigante. Valide fatos financeiros, evidências, tom e alegações de marca antes de devolver texto financeiro. Não streamar a resposta ainda não revisada.
Se política indisponível ou checagem falhar, fallback seguro e verdadeiro. Não alegar 100% de proteção. Integre Model Armor apenas se acesso confirmado e sem atrasar controles em código.

## Testes
Casos de prompt injection direto/indireto, alteração de persona, instrução SQL, saída com valor incompatível, resposta culpabilizante, oferta inventada, dados insuficientes, evento sem consentimento, modo demo ausente, off-topic benigno e falha do modelo. Reporte denominador, casos e falhas; não só uma nota agregada de um juiz LLM.

## Publicação
Ainda cedo, conferir permissões/read-only e runtime identity. Não mudar IAM para contornar bloqueio. Um serviço Cloud Run, UI compilada servida pelo FastAPI, escutando 0.0.0.0:$PORT. O ambiente Linux é construído na nuvem, não copie .venv Windows.
Pipeline do guia: Cloud Build -> Artifact Registry repo agentes -> Cloud Run us-central1 no projeto batalha-time-08-g7ha. Prefira imagem construída no repositório provisionado; --source pode criar outro repositório, portanto não presumir permissão.
GCP autentica por identidade de serviço/ADC e Secret Manager, mecanismo de Gemini confirmado; nada de chave JSON de SA. .dockerignore/.gcloudignore removem .git, .venv, node_modules, .env e dados locais. Logue apenas trace_id/latência/tools/estado, não extratos ou prompts completos.
Acesso público só com confirmação específica da equipe/organização; limitar demo a personas e endpoints autorizados. Projetos/contas pessoais não são fallback silencioso.
Config de custo/quota limita requisições e instâncias conforme o projeto; budget não é teto automático. Não criar banco novo para acompanhamento. Estado de demo é de sessão e não equivale a persistência de produção.
Verificar /health, uma análise real, recálculo e acesso da banca. Registre SHA e URL apenas após deploy bem-sucedido. Um único responsável publica.
