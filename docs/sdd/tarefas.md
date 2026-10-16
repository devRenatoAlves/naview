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
- [~] Usuário (e 2 ou 3 colegas) rodar o piloto e trazer o `relatorio-windows.txt`
- [ ] Fase 1: módulo `janelas` (X11 e Windows) e app reescrito em Qt (PySide6)
- [ ] Fase 2: jogo no `QWebEngineView` com `QWebChannel`
- [ ] Fase 3: pacote `.exe`, instalador e testes nos PCs da equipe
