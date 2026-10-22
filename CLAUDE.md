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
- **O NaView é para outras pessoas, em outros computadores e sistemas** (vários Linux, GNOME, KDE e
  Windows), não só para a máquina do dono. Toda mudança precisa funcionar assim: nada de caminho,
  usuário, ambiente de desktop, atalho ou configuração específicos desta máquina; mexer só em
  arquivos do usuário que o próprio app ou o instalador criaram; o que for só de um sistema fica
  atrás de `plataforma` e tem um caminho alternativo nos outros. Arte e fontes novas entram nos
  pacotes (`arte/`, `fonts/`). Se não der para testar em algum sistema, dizer qual.
- **O app precisa ficar sempre leve e fluido** (a equipe usa o dia todo, com sessões remotas
  abertas). Toda mudança visual ou de código é medida antes de entregar: nada de animação contínua
  sem necessidade, de timer que repinta a tela parada ou de efeito caro (desfoque, sombra grande,
  gradiente radial). Animações param quando a tela está escondida. Como medir: `docs/sdd/testes.md`.
- Siga os cuidados de `docs/sdd/testes.md`:
  - Sem print da tela inteira.
  - Sem conectar em clientes reais.
  - Sem alterar a configuração e o progresso reais do usuário.
- VPS do usuário: acesso por SSH. Antes de cada comando que mude algo nela, explique e peça
  confirmação. Senhas nunca passam pelo chat.
- Rodar o app: `python3 app.py`. O usuário abre pelo atalho do menu do KDE e precisa reabrir o app
  para ver as mudanças.

## Publicar uma nova versão

Quando o usuário pedir para publicar uma nova versão, siga estes passos (detalhes em
`docs/sdd/specs/07-atualizacao.md`). Sem subir o número da versão, ninguém recebe a atualização.

1. Rode `python3 ferramentas/nova_versao.py` (formato `AAAA.MM.DD.N`; só sobe o número, não commita).
2. Confira que `python3 ferramentas/gerar_site.py` roda e que `site/publico/download/versao.json`
   mostra a versão nova no Linux. Arquivo novo na raiz do app entra em `ARQUIVOS_APP` (ou
   `PASTAS_APP`) do `gerar_site.py`; se faltar, ele não vai no pacote nem na atualização. Se o
   Windows passar a ler um arquivo novo da pasta do app, ele precisa de `--add-data` no
   `.github/workflows/windows.yml`.
3. A árvore costuma ter muitas mudanças do usuário sem commit: mostre o que vai entrar e commite só
   o que ele aprovar. Nunca reverta o que não é seu.
4. Commit e push (o usuário pedir para publicar já autoriza). Push nesta máquina:
   `git -c credential.helper= -c credential.helper='!gh auth git-credential' push origin main`.
5. Explique o que acontece depois: o GitHub Actions monta o instalador do Windows (~15 a 20 min) e
   faz um commit novo em `site/windows/`; o Coolify refaz o site a cada push (confira o deploy pelo
   Coolify). Antes do próximo push, rode `git pull --rebase` para pegar o commit do instalador.
   O Linux recebe a versão assim que o primeiro deploy terminar; o Windows, quando o instalador
   novo estiver no site (cada sistema tem a sua versão em `versao.json`).
6. Confira o resultado: `curl -s https://naview.hunpe.com.br/download/versao.json` deve mostrar a
   versão nova nos dois sistemas.
7. Se for a primeira versão com o atualizador, avise: quem tem uma versão mais antiga precisa
   baixar de novo uma vez.
8. Registre a versão publicada em `docs/sdd/tarefas.md` e atualize o README se algo mudou para o
   usuário.
