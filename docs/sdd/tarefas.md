# Tarefas

Legenda: `[x]` feito, `[ ]` a fazer, `[~]` em andamento ou aguardando alguém.

## App de abas ([spec](specs/01-app-abas.md))

- [x] Encaixar a janela do AnyDesk em aba (XWayland)
- [x] Conectar por ID e detectar a janela pelo PID
- [x] Fechar aba e fechar o app encerrando as conexões
- [x] Corrigir o foco do teclado nas sessões encaixadas
- [x] Contatos importados do AnyDesk, com busca e renomear
- [x] Nome da aba atualizado automaticamente
- [x] Projeto renomeado para NaView (pastas de dados migradas sozinhas na primeira abertura)
- [x] Ícone novo: letra R em forma de veleiro (`icone.svg`)
- [x] Tema lendário Alto-mar (barco, mar e a marca da logo)
- [x] 7 pets novos: pinscher caramelo, corgi, salsicha, passarinho, Pikachu, Eevee e Jigglypuff
- [x] Pets redesenhados em pixel art 64 x 64 (sprites oficiais para os Pokémon) e Gengar
- [x] Barra de contatos retrátil
- [x] Corrigir a tela do jogo cortada quando o app abre com a barra lateral aberta
- [x] Atalho no menu de aplicativos (`.desktop`) e ícone próprio
- [x] Revisão da interface: ícones, cartão de conexão rápida, avatares, avisos, abas
- [x] Revisão de fluidez e usabilidade (15/10/2026): leitura do AnyDesk em cache, recentes na tela
  inicial, lista ordenada, Enter da busca corrigido, confirmação ao fechar sessão longa, jogo mais
  leve e liberado da memória
- [ ] Conferir em sessão real se o aviso do rodapé aparece por cima da janela do AnyDesk
- [ ] Testar com sessões reais: teclado, atalhos, tela cheia, transferência de arquivos
- [ ] Conferir o formato do título da janela de sessão (nome do computador) em sessão real
- [ ] Atalhos para trocar de aba (Ctrl+Tab, Ctrl+1..9)
- [x] Funcionar fora do KDE (GNOME e outros): vidro sem desfoque e mais opaco, instalador
  genérico que confere as bibliotecas, jogo com aviso se faltar o WebKit
- [x] Testado no GNOME por um amigo do usuário (15/10/2026): funcionou

## Temas ([spec](specs/02-temas.md))

- [x] Temas completos (fonte, arte e animações) e vidro líquido
- [x] Temas bloqueados na Aparência para quem não tem a carta
- [x] (21/10/2026) Tema Mangá Noir (preto e branco, anime, dark) com ícone do app próprio por tema; arte do usuário aplicada em 22/10/2026
- [x] (22/10/2026) Removidos ajustes de cor e imagem de fundo da janela Aparência; ícone do dock troca com o tema (reescreve o `naview.svg` do usuário)
- [x] (22/10/2026) Cabeçalho sem duplicação: tema só no jogo; ⋮ = Opções de aparência + Capturar janela (D38)
- [ ] Usuário abrir `python3 app.py` e `python3 app_qt.py`, escolher Mangá Noir e conferir visual e ícone (a parte Qt não foi rodada: sem PySide6 na máquina de desenvolvimento)

## Jogo ([spec](specs/03-jogo.md))

- [x] Fase 1: cartas, baús, recompensa diária, loja e pet Tamagotchi (local)
- [x] Ritmo lento de recompensas: coleção completa em ~4 a 8 meses
- [x] Nível da conta só como comemoração (as recompensas de nível foram removidas)
- [x] Simulador da economia (`ferramentas/simular_economia.py`)
- [x] Artes novas (15/10/2026): acessórios redesenhados pixel a pixel, petisco, moeda e baús com
  mais detalhe
- [x] Pet do rodapé sem o espaço vazio do quadro: todos os pets com o mesmo tamanho e centralizados
- [ ] Fase 2: missões diárias e mais cartas (efeitos, fundos)
- [ ] Dar uso às moedas que sobram; efeito de nível para todos os tipos de carta

- [ ] Redesenho do jogo (pedido de 22/10/2026), por etapas, cada uma mostrada ao usuário:
  1) cabeçalho (feito), 2) layout/organização da página do jogo (feito: pixel art, menu lateral, baús primeiro; aguardando aprovação do usuário), 3) baús e itens (feito e refeito em 32x28 com versão aberta), 4) pets próprios (feito: contorno seletivo, olhos novos, caras por humor e piscada; falta robô e salsicha com caras próprias)
- [x] (22/10/2026) Fredinho refeito a partir das fotos; pintinho e passarinho refeitos
- [x] (22/10/2026) Fredinho refeito como cópia do sprite-modelo do usuário, na cor do cachorro real
- [x] (22/10/2026) Ronaldo refeito como cópia do sprite-modelo do usuário, na cor do cachorro real
- [x] (22/10/2026) Acessórios reencaixados nos pets de lado (Fredinho, Ronaldo, passarinho) e conferidos nos 14 pets
- [x] (22/10/2026) Reformulação dos pets: saíram corgi, passarinho, pintinho, fantasma e robô; entraram
  gato preto, Jonatas, astronauta, serpente de gelo (GIFs animados), galinha e slime (PNGs); acessórios
  encaixados; migração do progresso antigo (D46)
- [x] (22/10/2026) Nome do pet fixo, o da espécie; renomear removido (D47)
- [ ] Usuário abrir `python3 app.py`, conferir os pets novos (animação na tela do pet, rodapé, acessórios)
  e a parte Qt (`app_qt.py`, só compilada: sem PySide6 aqui)
- [ ] Caras por humor (pisca, feliz, triste) para o slime e a galinha, se o usuário quiser
- [x] Usuário escolheu pixel art (22/10/2026). Só MIT/CC0, sem créditos na tela (game-icons.net, CC BY, fica de fora)

## Servidor da equipe ([spec](specs/04-servidor.md))

- [~] Usuário confirmar o plano do AnyDesk (API REST)
- [~] Usuário passar os dados da VPS (endereço, usuário SSH, sistema, o que já roda, domínio)
- [ ] Definir os prêmios reais e os critérios
- [ ] Fase 1: servidor (API + contas + `Progresso` por colaborador) e login no app
- [ ] Fase 1: `ProgressoRemoto` no app e fila de atendimentos sem internet
- [ ] Fase 1: instalação na VPS (serviço, HTTPS, backup do banco)
- [ ] Fase 2: migrar o progresso local do usuário
- [ ] Fase 3: conferir os atendimentos pela API do AnyDesk
- [ ] Fase 4: ranking, prêmios e painel do administrador

## Página de apresentação ([spec](specs/05-landing.md))

- [x] Pesquisar as ferramentas (skills) mais usadas para landing pages
- [x] Instalar `ui-ux-pro-max` (em `.claude/skills`) e o plugin `playwright` (escopo do projeto)
- [x] `impeccable` descartado (baixa um programa compilado; o visual já fica coberto)
- [x] Criar a página (design, seções, download)
- [x] Gerar o pacote de download com versão e SHA-256 (`ferramentas/gerar_site.py`)
- [x] Repositório privado no GitHub: `devRenatoAlves/naview` (ramo `main`)
- [~] Usuário criar o subdomínio `naview.hunpe.com.br` apontando para a VPS
- [ ] Publicar na VPS pelo Coolify (domínio e HTTPS)
- [ ] Testar o download e a instalação a partir do site publicado
- [x] (15/10/2026) Revisão do topo: trocar de tema não move mais título, botões, janela nem cartas;
  fontes dos temas carregadas no início; abas da demonstração encolhem com reticências
- [x] Publicar a revisão do topo (no ar em 15/10/2026; CSS e JS com `?v=` contra cache antigo)
- [x] Página de teste `/gnome/` usada e removida; a página principal agora fala só "Linux"

## Windows ([spec](specs/06-windows.md))

- [x] Levantar o que serve, o que quebra e o caminho (Qt nos dois sistemas)
- [x] Script do teste de viabilidade (`ferramentas/teste_windows.py`)
- [x] Piloto para a equipe: `.exe` montado pelo GitHub Actions e página `/piloto/` no site
- [x] Primeira montagem no GitHub Actions (15/10/2026): `.exe` abre, zip de 40 MB publicado em `/piloto/`
- [x] Primeiro teste do usuário (16/10/2026): não conectou e travou. Piloto refeito: conectar
  separado do encaixe, três modos de encaixe, registro em arquivo e aviso de travamento
- [x] Usuário rodou o piloto (16/10/2026): passou em tudo (ver spec, Situação)
- [ ] 2 ou 3 colegas rodarem o piloto: NaView sem administrador, escala 125%/150%, antivírus
- [x] Fase 1: `plataforma.py`, módulo `janelas` (X11 e Windows) e `app_qt.py` com abas, contatos,
  recentes, temas, Aparência, pet, avisos e teclado (16/10/2026)
- [x] Fase 2: jogo no `QWebEngineView` com `QWebChannel`, sem mudar `web/jogo.js` (16/10/2026)
- [ ] Usuário testar `python3 app_qt.py` no dia a dia (Linux) e apontar diferenças
- [ ] Trocar o atalho do menu e o `instalar.sh` para a versão Qt; depois apagar `app.py`,
  `janela_aparencia.py`, `jogo/gtk.py`, `jogo/tela.py`, `fontes.py` e o CSS do GTK em `temas.py`
- [x] Fase 3 (montagem): PyInstaller + Inno Setup no GitHub Actions (`windows.yml`)
- [x] Decidir onde publicar o instalador: no repositório, enxugado para 92,7 MB (D35)
- [x] Página com a escolha Linux | Windows, lendo `download/windows/windows.json` (16/10/2026)
- [ ] Se o instalador passar de 100 MB: plano B pela VPS (ver spec 05)
- [ ] Testar o instalador nos PCs da equipe: com e sem administrador, escala 125%/150%, antivírus,
  contatos do AnyDesk no Windows (`%APPDATA%\AnyDesk\user.conf`)

## Atualização automática ([spec](specs/07-atualizacao.md))

- [x] Manifesto `download/versao.json` no `gerar_site.py` e no `nginx.conf` (22/10/2026)
- [x] `atualizador.py` (consulta, baixa, confere o SHA-256, troca no Linux, instalador no Windows)
- [x] Botão "Atualizar" no GTK (`app.py`) e no Qt (`app_qt.py`)
- [x] `ferramentas/nova_versao.py` (formato `AAAA.MM.DD.N`)
- [x] Teste de ponta a ponta no Linux (pacote local) e de interpretação do manifesto
- [ ] Testar o Qt com PySide6 (botão na barra, thread, fechamento) no Linux e no Windows
- [x] Correções do teste no Windows (22/10/2026), falta reconferir no Windows: botão dos contatos
  voltou ao canto esquerdo da barra (título fora do layout); linhas de contato com altura fixa
  mínima (avatares cortados); "Meu AnyDesk: ID" no topo dos contatos (clique copia), lido de
  `ad.anynet.id` (`system.conf`) ou de `anydesk --get-id`
- [x] "Meu AnyDesk" também no GTK (`app.py`, usado no Linux), versão `2026.10.22.3` (22/10/2026)
- [ ] Testar a atualização no Windows: instalar uma versão, publicar outra, clicar em Atualizar
- [x] Versão `2026.10.22.1` (primeira com o atualizador, junto com a reformulação dos pets) enviada em 22/10/2026
- [ ] Avisar a equipe para baixar o NaView de novo uma vez (versões antigas não têm o atualizador)
- [x] Versão `2026.10.22.2` (correções do teste no Windows + ID do AnyDesk) enviada em 22/10/2026; falta provar a atualização no Windows
- [ ] Mais tarde, se a equipe crescer: assinar o manifesto

- [x] Windows: colar na sessão parava de funcionar depois de sair e voltar ao NaView. Diagnóstico
  (`ferramentas/diagnostico_colar_windows.py`, 22/10/2026): ao reativar, o foco ficava na janela do Qt e
  não na do AnyDesk. Correção: `restaurar_foco` (`janelas/win32.py`), chamado ao reativar a janela
  (`app_qt.py`). **Falta reconferir no Windows** (sair para outro programa, voltar e colar).
- [x] Versão `2026.10.22.4` (correção do colar/foco no Windows) enviada em 22/10/2026; falta reconferir no Windows
- [ ] Perfil dos colegas (ver inventário uns dos outros, só leitura): planejado em `specs/04-servidor.md` (R10 a R14); começa depois do servidor e do login
- [x] Windows: foco do teclado por eventos (`observar_foco`, `on_evento_foco`): Win+V e Ctrl+V voltavam a falhar depois de um tempo; agora a sessão tem prioridade e clique em campo de texto do NaView tem prioridade sobre ela. **Falta testar no Windows** e publicar (versão ainda não subida)
- [x] Versão `2026.10.22.5` (foco do teclado por eventos no Windows + SDD do perfil dos colegas) enviada em 22/10/2026; falta reconferir no Windows

- [ ] (22/10/2026) Sessão preta no GNOME com tema Vidro: janela sem alfa fora do KDE (D49). Falta o usuário confirmar com `python3 app.py` (e, se ainda ficar preta, `NAVIEW_JANELA_ALFA=0`/`1` para comparar)
- [x] Versão `2026.10.22.6` (janela opaca fora do KDE no GTK, hipótese da sessão preta no GNOME) enviada em 22/10/2026
