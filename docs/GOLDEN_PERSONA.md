# Golden persona — origem, limites e reprodução

Atualizado em 2026-09-27. **Persona derivada da base sintética do hackathon. Não representa cliente real do Itaú.**

Identificador sintético autorizado: `6491f4a4-67dc-49de-a38a-cf655ff77c33`. Referência reproduzível: **2025-09-30**. Fonte esperada no runtime publicado: `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`, dataset em `us-central1`.

**Fonte do snapshot:** anexo do usuário `Texto colado.txt`, na rodada “GOLDEN PERSONA REAL + DEMO CONVERSACIONAL FINAL”. Os fatos abaixo foram fornecidos nesse anexo como observações da base. **Eles não são resultado de uma nova consulta executada nesta rodada.** `tests/fixtures/golden_persona.json` preserva somente os valores fornecidos, com `origin=user_supplied_hackathon_snapshot`.

**VERIFICADO localmente:** carregamento explícito da fixture e conversão de agregados com cliente BigQuery falso; 21 testes novos de dados e 17 testes anteriores do adaptador passaram. **VERIFICADO agora no Google:** SQL golden/CLT real e jornada local com Gemini/BigQuery PASS, evidência em EXECUCAO_GOLDEN_REAL_2026-09-27.md. Nova revisão Cloud Run não publicada por bloqueio na leitura de IAM ancestral; não confundir a validação local real com publicação.

## Fatos fornecidos

Todos os valores desta tabela estão em BRL. As margens são salário menos gastos sem fatura, não saldo, renda disponível garantida nem avaliação de crédito.

| Mês de 2025 | Salário CLT | Gastos sem fatura | Margem histórica | Flexíveis fornecidos | Juros observados |
|---|---:|---:|---:|---:|---:|
| Abril | 6.754,99 | 7.222,61 | -467,62 | 84,66 | 0,00 |
| Maio | 6.754,99 | 6.361,45 | 393,54 | 378,34 | 0,00 |
| Junho | 6.754,99 | 9.363,19 | -2.608,20 | 985,59 | 0,00 |
| Julho | 6.754,99 | 4.938,50 | 1.816,49 | 200,89 | 0,00 |
| Agosto | 6.754,99 | 7.383,33 | -628,34 | 349,13 | 0,00 |
| Setembro | 6.754,99 | 7.331,84 | -576,85 | 386,47 | 0,00 |

Cálculo determinístico, arredondado ao centavo: média da margem de julho–setembro **R$ 203,77**; média dos seis meses **-R$ 345,16**. A variação é material: a média recente não é promessa de capacidade futura. A fixture não inclui médias constantes; o engine calcula a partir dos meses.

Categorias relevantes de setembro fornecidas pelo usuário:

| Categoria | Valor BRL |
|---|---:|
| Emprestimos e financiamentos | 3.222,61 |
| Educação | 1.485,96 |
| Casa | 1.289,30 |
| Mercado | 568,23 |
| Posto | 280,50 |
| Viagens | 244,01 |
| Restaurantes | 60,88 |
| Produtos financeiros | 49,67 |

São categorias selecionadas, não o extrato completo. Sua soma, R$ 7.201,16, não equivale ao total de gastos de setembro; categorias/valores faltantes não foram inventados. O anexo também informou parcela imobiliária de R$ 3.222,61, faculdade de R$ 1.485,96 e pagamento integral de fatura de R$ 1.378,48. Esses movimentos não são automaticamente obrigações futuras. O pagamento da fatura não é somado novamente às despesas usadas nesta comparação; isso é uma regra explícita de visão de despesas, **não conciliação bancária completa**.

## Parcelas observadas e projeção condicional

| Rótulo seguro | Parcela BRL | Índice observado | Restantes pelo marcador | Término estimado fornecido |
|---|---:|---:|---:|---|
| Passagem aérea | 244,01 | 2/3 | 1 | 2025-10-10 |
| IPTU | 411,09 | 9/10 | 1 | 2025-10-12 |
| Artigos infantis | 35,68 | 5/6 | 1 | 2025-10-18 |

Soma calculada: **R$ 690,78**. O anexo não forneceu as datas originais das observações, somente os términos estimados. Por isso, a fixture usa `last_observed_date=null`; não deduz artificialmente dias de setembro a partir dessas estimativas. Também não possui contagem de transações, cobertura diária fictícia ou descrição livre. Os rótulos acima substituem descrições livres por nomes definidos no código.

No modo BigQuery, cada parcela devolvida vem de uma saída observada em setembro com índice atual menor que o total. `last_observed_date` vem da linha consultada; `estimated_end_date` usa a função existente `shift_months_clamped(data, total-current)`. Essa hipótese pressupõe periodicidade mensal e mesmo valor, e mantém `requires_confirmation=true`. Marcadores não comprovam quitação, contrato ativo ou agenda completa. Nenhuma parcela histórica é inserida em `scheduled_cashflows`.

O comparativo condicional usa a **composição de setembro**, que inclui as três parcelas. Se as três terminarem e os demais componentes de setembro se repetirem, o indicador antes do novo aparelho passa de -R$ 576,85 para **R$ 113,93** (-576,85 + 690,78). Não somar essa liberação à média trimestral como se todas essas parcelas estivessem presentes, com os mesmos valores, em todos os meses. Nem o indicador condicional nem a média são projeção de saldo.

## Adapter e interface

O modo legado permanece inalterado por padrão. O backend ativa a extensão explicitamente:

```python
from datetime import date
from backend.data.bigquery_context import BigQueryContextProvider

provider = BigQueryContextProvider(
    authorized_users=backend_bound_alias_to_id,
    reference_date=date(2025, 9, 30),
    golden_persona=True,
)
context = provider.get_context(backend_bound_alias)
golden = context.historical_summary['golden']
```

`authorized_users` vem de configuração confiável do backend. Request/modelo não escolhem identidade, tabela, projeto, referência ou SQL. `get_financial_context` também verifica a allowlist. A referência golden diferente de 2025-09-30 é rejeitada antes de consulta. O responsável pela API impõe a única identidade sintética autorizada; a allowlist isolada não é autenticação multicliente.

Estrutura adicional, sem mudar o contrato antigo:

```text
golden = {
  reference_date: "2025-09-30", currency: "BRL",
  origin: "dataset_observed" | "user_supplied_hackathon_snapshot",
  monthly: [{month: "YYYY-MM-01", salary_cents: int|null,
             expenses_excluding_invoice_cents: int,
             flexible_cents: int|null, interest_cents: int}],
  installments: [{label: safe_label, amount_cents: int, current: int, total: int,
                  last_observed_date: "YYYY-MM-DD"|null,
                  estimated_end_date: "YYYY-MM-DD", requires_confirmation: true}],
  categories: [{category: string, amount_cents: int}],
  limitations: [string]
}
```

A conversão para BRL vale somente para a persona golden explicitamente confirmada pelo anexo. O adapter legado preserva moeda desconhecida e montantes `_units`. A consulta golden arredonda cada FLOAT em duas casas e converte para NUMERIC antes de agregar; Python valida Decimal e converte em centavos inteiros. Saldo, margem protegida e agenda continuam respectivamente `None`, `None` e `[]`.

`golden_context.sql` faz um único SELECT agregado de abril a setembro, precedido de dry-run. Preserva o teto de 1 GiB, timeout de 20 segundos, job timeout, cancelamento best-effort e ausência de retries automáticos do adapter existente. Resposta limitada a 50 mil caracteres, seis meses, 12 categorias e 12 parcelas individuais; truncamento das listas é declarado nas limitações. Ausência de mês não vira mês com zero.

Classificações predefinidas:

- **Salário CLT:** somente `tipo='E'` com microcategoria ou descrição exatamente `salario clt` após normalização de acentos, caixa e espaços externos. Outras entradas não são salário. Sem correspondência explícita, `salary_cents=null`. A consulta real de 27/09/2026 reconheceu esse critério e reproduziu os seis salários do snapshot; não foi necessário alterar o SQL.
- **Gastos sem fatura:** saídas cuja microcategoria é diferente de `Pagamento de fatura`. Categorias de setembro usam o mesmo recorte. Transferências não são removidas por suposição.
- **Juros:** saídas de microcategoria `Juros pagos`, já identificada no diagnóstico. Ausência nessa categoria é zero observado, não prova de ausência de juros futuros.
- **Flexíveis:** a regra original não foi fornecida. A fixture mantém os valores do anexo; runtime retorna `flexible_cents=null` até definição verificada. Não foi inventada uma lista de categorias flexíveis.
- **Parcelas:** somente saídas do mês de referência com `parcela_atual < parcela_total`. Descrições são usadas apenas dentro do BigQuery para rótulos fixos Passagem aérea/IPTU/Artigos infantis/Parcela observada; nunca enviadas ao agente.

A normalização segue [funções de string GoogleSQL](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/string_functions#normalize); o alias reservado `current` é escapado segundo a [sintaxe GoogleSQL](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/lexical#reserved_keywords). Esses referenciais não substituem um dry-run real.

## Fixture offline e falhas

```python
from backend.data.golden_fixture import load_golden_fixture
context = load_golden_fixture()
```

O loader só lê `tests/fixtures/golden_persona.json`; não reconstrói valores se o arquivo faltar. A API exige seleção offline explícita. O loader recusa execução com `K_SERVICE`, e a fixture não integra o pacote Cloud Run. `EvidenceOut.origin=user_confirmed` preserva o enum existente e significa snapshot fornecido pelo usuário; o detalhe e `history.origin` deixam explícito que é offline. Isso não alega consulta real.

O provider BigQuery não importa nem chama esse loader. Erro de permissão, timeout ou payload inválido permanece `DataProviderError`; não há troca por fixture. O código real nunca usa os valores monetários ou o identificador da fixture como constante de resultado.

## Comportamento esperado e hipóteses do cliente

O fluxo iPhone de R$ 10.000 começa perguntando a forma de pagamento. “10 vezes sem juros” é condição informada pelo cliente; o engine calcula 10 parcelas de R$ 1.000. A resposta deve mostrar margem volátil, setembro negativo e término estimado das parcelas, com a ressalva de que esperar não garante uma compra segura.

Entrada informada de R$ 2.000 deixa R$ 8.000. Com 12 parcelas sem juros informadas, o engine preserva centavos: **8 parcelas de R$ 666,67 e 4 de R$ 666,66**. Não existe oferta de loja/banco confirmada. Esperar novembro altera a comparação condicional, sem inventar renda ou saldo. Necessidade profissional recebe acolhimento; decisão final continua com a pessoa. Supervisor permanece opt-in, sem notificação real, usando somente evento simulado autorizado.

## Evidências e próximo teste real

Execução em 2026-09-27:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_golden_data.py tests/test_data.py -q
# 38 passed: 21 golden + 17 anteriores do adapter.
```

O ciclo inicial foi vermelho por ausência do loader/flag (`17 failed`), seguido de implementação e casos adicionais. A suíte agora cobre valores fornecidos, centavos consultados diferentes da fixture, data fixa, projeção de fim de mês, salário desconhecido, ausência de dados, autorização/SQL injection, limites de custo, payload inválido, falha sem fallback, arquivo ausente e proibição de fixture em Cloud Run. Usa SDK real com cliente falso; **não prova compilação nem execução SQL no Google**. Contagem global/testes de engine, conversa e evals são registrados pelo integrador em STATUS-CORE/EVAL_REPORT.

Roteiro de validação externa, agora executado com sucesso (repetir quando necessário ao publicar): executar somente o adapter acima com a identidade golden imposta no servidor, mantendo dry-run antes do SELECT; comparar os seis meses e as três parcelas com o snapshot sem publicar IDs, descrições ou extrato. Conferir que o rótulo explícito CLT é reconhecido; se divergir, inspecionar apenas agregados/rótulos necessários e corrigir o critério predefinido com evidência. Não generalizar toda entrada para salário, não ajustar SQL para devolver constantes esperadas e não inventar regra para flexíveis. Registrar job/estado/providers e discrepâncias de forma sanitizada. Só depois seguir os testes da API real e a publicação autorizada da nova revisão.
