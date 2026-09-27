# Dados — agora adaptador, não mais exploração ampla

Leia as instruções existentes, 00_COMECE_AQUI.md, 01_ESPECIFICACAO.md e contracts/. O nome é Pingo. Este v2 estende o v1 sem autorização para sobrescrever trabalho em andamento. Faça revisão curta de compatibilidade/contrato com Vinicius; após a aprovação de escopo e plano, implemente em sua branch/worktree. Não repetir descoberta ampla nem automatizar login novamente. Claude/Codex são ferramentas de desenvolvimento; o produto usa somente Gemini autorizado. Não exportar dados do evento, commitar segredos, alterar IAM, faturamento ou publicar sem autorização específica. Fixture deve ter modo visível; não dizer que integração real passou sem testar. Não fazer mudanças fora da faixa de arquivos sem coordenação.

## Faixa
backend/data/, sql/, docs/DADOS.md. A interface get_financial_context é fixada pelo integrador em backend/core/context_contract.py; não invente uma segunda estrutura de retorno.

## Já disponível
HISTORIAS_DOS_DADOS.md registra 467.585 linhas, 1.000 usuários e 2025 completo, região us-central1. Existem marcadores históricos de parcela_atual/parcela_total, mas não vencimentos futuros, taxas ou saldo atual confirmado. Não repetir as 12 análises; use schema/SQL do diagnóstico que está no notebook.

## Entrega
1. Normalização e consultas parametrizadas para uma persona autorizada: estatísticas por mês/categoria e candidatos de recorrência/parcelamento. Leitura da tabela exata batalha-time-08-g7ha.hackathon_dados.extrato_sintetico.
2. Identidade vem do servidor/allowlist; não aceitar ID instruído pela LLM. Nenhum SQL livre gerado pelo modelo.
3. Separar fatos observados, estimativas e campos ausentes. Não mapear entrada diretamente para salário. Não eliminar toda fatura indiscriminadamente para a conta caber; separar visão de caixa e consumo/assumptions.
4. Permitir uma persona sintética da base como demo principal e outra contrastante. Não escolher apenas história favorável. Saldo/agenda futura para a demo são complementos explicitamente confirmados/ilustrativos, não colunas da base.
5. Testes unitários de normalização com fixtures próprias e teste de integração real somente no ambiente autorizado. Marque o que não pôde executar.
6. Consultas com limite de bytes e sem exportar a base. Credenciais não entram no Git. O código pode ser escrito fora, mas processamento dos dados deve permanecer nos destinos permitidos.

Bloqueio de integração vira erro técnico + pergunta objetiva ao mentor. Não parar todo o time e não tentar contornar login automatizado. Resultado útil agora é código adaptador testável e um exemplo de retorno aceito pelo core.
