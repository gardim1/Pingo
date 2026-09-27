# Histórico do acesso e comandos de metadados

O Google recusou o login na janela automatizada do `agent-browser` com a mensagem "Esse navegador ou app pode não ser seguro". A sessão foi encerrada sem contornar a proteção. Depois, a extensão oficial `@Chrome` acessou a aba do Google Cloud já autenticada pelo usuário; o Cloud Shell funcionou. Os comandos de metadados abaixo foram executados e confirmaram o schema e a localização. Não é necessária intervenção manual para esta rodada.

```bash
bq --project_id=batalha-time-08-g7ha show --format=prettyjson batalha-time-08-g7ha:hackathon_dados | python3 -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps({"dataset":d.get("datasetReference",{}).get("datasetId"),"location":d.get("location")},ensure_ascii=False,indent=2))'
bq --project_id=batalha-time-08-g7ha show --format=prettyjson batalha-time-08-g7ha:hackathon_dados.extrato_sintetico | python3 -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps({"schema":d.get("schema",{}).get("fields",[]),"numRows_metadata":d.get("numRows"),"numBytes_metadata":d.get("numBytes"),"timePartitioning":d.get("timePartitioning"),"rangePartitioning":d.get("rangePartitioning"),"clustering":d.get("clustering")},ensure_ascii=False,indent=2))'
```

Os números `numRows_metadata` e `numBytes_metadata` são metadados; a consulta de contagens foi executada separadamente. O registro das 12 consultas, dry-runs e bytes está em `sql/README.md`. O limite desta rodada foi atingido; não executar mais consultas de dados sem nova autorização do time. Não colar credenciais, tokens, IDs individuais nem linhas de extrato.
