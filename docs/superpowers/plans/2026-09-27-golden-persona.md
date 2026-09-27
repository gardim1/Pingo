# Golden persona — execução autorizada

Pedido integral no anexo do usuário; sem brainstorming, browser, frontend, deploy automático ou refactor amplo. Preservar publicação anterior e distinguir nova revisão pendente.

- [x] Ler estado/código/contratos; baseline 103 testes e 18 evals PASS.
- [x] Adapter BigQuery opcional para fatos golden, snapshot só offline explícito.
- [x] Identidade/data impostas no servidor, origem runtime explícita, sem fallback.
- [x] Conversa + comparação histórica condicional com centavos exatos; saldo permanece desconhecido.
- [x] Reutilizar acompanhamento consentido com evento único simulado.
- [x] Testes de regressão, evals golden, smoke; revisão independente.
- [x] Documentar fonte/limites/API e prompt para publicar nova revisão.

Não alterar schemas v1 de resposta. Campos opcionais de condições/conversa podem ser acrescentados preservando requests atuais. Parcelas sem data permitem cotação matemática rotulada; cronograma datado só após data informada. Comparação de média histórica + término estimado não representa saldo ou renda disponível garantida. Valores livres do LLM não chegam à resposta.

Validação final local: 147 pytest PASS (103 anteriores + 44 novos), 18 evals anteriores e 23 golden PASS, pip check saudável, smokes HTTP legado/golden PASS. Revisão independente concluída. Adapter golden verificado com transporte falso; SQL/CLT real, Gemini golden ao vivo e nova publicação continuam pendentes no handoff. ADC local bloqueado por TLS; nenhum deploy desta rodada.
