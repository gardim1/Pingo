# Um projeto compartilhado, não uma pasta compartilhada

## Se já há código
Primeiro `git status` e `git remote -v`. Não criar outra raiz ou apagar o trabalho. Se a pasta atual é só diagnóstico, preservar docs/SQL e criar o app nessa raiz ou em repositório separado combinado; documentação deve entrar no único repo final sem extratos/segredos.

## Criar a origem comum
Uma pessoa cria `pingo` privado na conta/equipe autorizada e adiciona os outros três como colaboradores com acesso de escrita. Não usar GitHub público nem repositório profissional da Suno. A autorização do evento para código externo continua necessária. Não dar credenciais compartilhadas: cada colega usa sua conta.

O integrador publica primeiro a base: README, .gitignore, contratos, fixtures próprios e diretórios. Só então os demais clonam o mesmo repositório e criam a branch de sua frente. Se já há frontend, manter sua stack.

## Operações após clonar e confirmar que a árvore está limpa
Para a pessoa do frontend (as demais trocam apenas a branch):
```bash
git switch main
git pull --ff-only origin main
git switch -c feat/ui
```
Se a branch já existir, usar `git switch feat/ui`, sem recriar.
Após trabalhar, selecionar arquivos explicitamente (não fazer git add indiscriminado):
```bash
git add frontend/
git commit -m "feat: primeira tela de planejamento"
git push -u origin feat/ui
```
Abrir pull request para main. Vinicius revisa/testa e integra; só main testada vai para a demo. Um incremento pequeno por vez — não esperar o fim da tarde para juntar tudo.

Para trazer atualizações com sua branch limpa:
```bash
git fetch origin
git merge origin/main
```
Se houver conflito, parar e resolver com o dono. Não force-push e não resetar para apagar o conflito.

## Dois agentes no MESMO notebook
Cada um precisa de checkout/worktree separado, além da branch. Não basta pedir branches diferentes em duas conversas que compartilham a mesma pasta.
Se o repo principal está em feat/core, a pessoa coordenadora pode preparar o frontend em outra pasta a partir da base publicada (se essa branch/pasta ainda não existe):
```bash
git fetch origin
git worktree add ../pingo-ui -b feat/ui origin/main
```
Apenas o executor de UI abre ../pingo-ui; core continua no original. Verificar worktrees existentes primeiro. Nunca adicionar worktree sobre pasta de outro projeto.

## Regras da equipe
- Mesmo repositório; branches e pastas de trabalho separadas.
- Contratos, versões e nomes compartilhados pertencem ao integrador.
- Dados do evento/credenciais fora do Git; usar .gitignore e .gcloudignore.
- Um único responsável pelo deploy evita trocar a demo por builds incompatíveis.
- AGENTS.md/CLAUDE.md apontam para esta spec e para docs/STATUS-[frente].md.
- Atualização de 3 linhas em cada marco: funciona, teste executado, bloqueio. Mais código testado e menos relatórios longos.
