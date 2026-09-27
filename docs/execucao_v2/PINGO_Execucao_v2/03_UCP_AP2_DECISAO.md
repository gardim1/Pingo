> Atualização v2: 01_ESPECIFICACAO.md e 00_COMECE_AQUI.md prevalecem. UCP/AP2/Jev fora do primeiro corte; modos de acompanhamento e colaboração estão especificados nos documentos v2.

# Pesquisa: o que o colega citou e se entra no Pingo

Verificado em 26/09/2026 em fontes primárias listadas em 08_FONTES.md.

## Identificação
UCP = Universal Commerce Protocol. Padrão aberto para integração entre superfícies/agentes e negócios de comércio: descoberta de capacidades, catálogo/conforme capacidades, carrinho, checkout e pedidos.
AP2 = Agent Payments Protocol. Autorizações verificáveis/mandatos que vinculam intenção, condições e pagamento. Não é calculadora de fluxo de caixa nem mecanismo que prova que a compra é boa para a pessoa.
A2A = Agent2Agent. Comunicação entre aplicações de agentes; não é necessário só porque funções ou subagentes coexistem no mesmo app.
ADK = Agent Development Kit. Framework para construir o agente e suas ferramentas; não confundir com UCP/AP2.

## O que as fontes sustentam
Há samples públicos UCP, inclusive servidor Python/FastAPI e cliente; o sample mostra descoberta, sessões de checkout e simulações. Há samples AP2 com ADK e Gemini, incluindo jornadas com usuário presente.
UCP/AP2 não conectam automaticamente ao Itaú Shop, não revelam estoque de qualquer loja e não liberam cartão do Google Wallet. Um lojista/PSP compatível, credenciais, onboarding e autorizações continuam sendo necessários.
Ser open source/relacionado ao Google não equivale a autorização do evento. Não há evidência de acesso a APIs internas Itaú nesta conversa.

## Minha recomendação
Core = decisão financeira e plano revisável.
Extra possível = checkout demonstrativo de loja local própria, usando um sample oficial UCP isolado, só após o core funcionar.
AP2 = opcional e mais exigente; só integrar se um sample verificável couber no tempo e os testes de assinatura/consentimento passarem. A alternativa padrão é retirar AP2 da demo, não fingir conformidade.
A2A = não adicionar ao core para inflar arquitetura. Se um sample externo já o usa, não fazer a banca confundir integração demonstrativa com necessidade do motor financeiro.

## Experimento isolado — limite sugerido 30 minutos após o core
1. Confirmar permissão de dependências open source e ambiente local de demo.
2. Ler README do sample oficial e fixar commit/versões compatíveis; exemplos antigos e schema atual podem divergir.
3. Subir apenas merchant mock + cliente numa pasta/worktree separada, sem alterar o app principal.
4. Mostrar descoberta, oferta fictícia com preço/condições explícitos, criação/revisão de checkout, consentimento para simular e resultado de teste.
5. Demonstrar preço alterado após confirmação: exigir revisão; não finalizar silenciosamente.
6. Se o sample não ficar funcional e compreensível no limite, desligar. Registrar como oportunidade futura.

Não começar pelo sample completo com vários agentes, vários serviços e UI própria só por parecer pronto: ele pode consumir mais integração que nosso próprio núcleo.
Não trocar a jornada de bem-estar por um funil para vender um celular.

## O que dizer na banca
Com UCP validado: 'Depois da análise, demonstramos como um checkout de comerciante simulado pode ser conectado usando esta implementação do padrão UCP; não há integração com Itaú Shop nem pagamento real.'
Sem protocolo implementado: 'A jornada pode futuramente se integrar a padrões abertos de comércio. Na demo, mostramos somente o plano e a confirmação simulada.'
Com apenas recibo/hash local: chamar 'registro de consentimento do protótipo', nunca 'AP2 implementado'.

## Requisitos que tornam AP2 mais que um hash
A extensão UCP/AP2 exige negociação de capacidade, assinaturas do comerciante, mandatos/credenciais assinados vinculados às condições e verificação pelas partes. O schema atual não é idêntico a exemplos antigos. Canonicalização, identidade confiável, verificação, prazo/estado, alteração e repetição devem seguir a versão escolhida.
Chave criada pelo próprio demo representa identidade de teste, não autenticação de usuário real. Um checkbox ou SHA-256 sozinho não comprova autoria nem autorização bancária.
No Pingo, mesmo em teste, usar fluxo human-present: confirmação explícita do usuário a cada conjunto final de condições. Não configurar compra autônoma futura.
