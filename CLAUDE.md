# NaView

App GTK3 (Python) que junta as conexões do AnyDesk em abas, com temas e um jogo de coleção para
a equipe de suporte (~10 colaboradores).

## Antes de começar

Leia `docs/sdd/README.md` (índice e situação geral) e `docs/sdd/tarefas.md`. A especificação de
cada parte fica em `docs/sdd/specs/`, e as decisões tomadas em `docs/sdd/decisoes.md`.

## Ao trabalhar

- A cada progresso, atualize a spec afetada, `docs/sdd/tarefas.md` e, se houve escolha
  importante, `docs/sdd/decisoes.md`. Atualize também o README quando mudar algo que o usuário vê.
- Mudou um número da economia do jogo? Rode `python3 ferramentas/simular_economia.py` e atualize a
  tabela em `docs/sdd/specs/03-jogo.md`.
- Siga os cuidados de `docs/sdd/testes.md`:
  - Sem print da tela inteira.
  - Sem conectar em clientes reais.
  - Sem alterar a configuração e o progresso reais do usuário.
- VPS do usuário: acesso por SSH. Antes de cada comando que mude algo nela, explique e peça
  confirmação. Senhas nunca passam pelo chat.
- Rodar o app: `python3 app.py`. O usuário abre pelo atalho do menu do KDE e precisa reabrir o app
  para ver as mudanças.
