# 06: NaView no Windows (fase 1 em andamento)

## Objetivo

O mesmo programa no Windows 10 e 11: abas com as sessões do AnyDesk encaixadas, contatos,
recentes, temas, jogo e, depois, o servidor da equipe. O usuário pediu um programa **idêntico**
(15/10/2026).

## Requisitos

- R1. Tudo o que o app faz no Linux (specs 01 a 03), com o mesmo visual e o mesmo comportamento.
- R2. Um código só para os dois sistemas. Só a parte que conversa com o sistema muda.
- R3. Instalação simples: instalador `.exe`, atalho no menu Iniciar, sem pedir Python.
- R4. Os mesmos cuidados de leveza: nada pesando com uma sessão aberta.

## O que já serve e o que não serve

| Parte | Situação no Windows |
|---|---|
| `jogo/progresso.py`, `jogo/catalogo.py` | Serve como está (Python e SQLite) |
| `web/` (jogo) | Serve; muda só a ponte `chamar()` (de `webkit.messageHandlers` para `QWebChannel`) |
| `arte/`, `sons/`, `fonts/`, ícones | Servem como estão |
| `contatos.py` | Muda a pasta: `%APPDATA%\AnyDesk\user.conf` (formato a confirmar) |
| `x11.py`, `Gtk.Socket` | Não existem no Windows: encaixe com a API do Windows |
| `app.py`, `janela_aparencia.py`, CSS do GTK em `temas.py` | GTK3 no Windows é ruim e não tem WebKit: reescrever em Qt |
| Vidro (desfoque do KDE) | Trocar pelo Mica/Acrylic do Windows 11 (`DwmSetWindowAttribute`) |

## Design proposto

- **Qt (PySide6) nos dois sistemas**, em vez de GTK3:
  - Encaixe: `QWindow.fromWinId` + `QWidget.createWindowContainer`. No Windows recebe o
    identificador da janela (HWND); no Linux, a janela do X11. O mesmo código serve aos dois.
  - Jogo: `QWebEngineView` no lugar do WebKit2GTK.
  - Temas: folha de estilo do Qt (QSS) gerada a partir das mesmas cores e artes; as animações da
    tela inicial passam para `QPropertyAnimation`.
- **Módulo `janelas`** com a mesma interface nos dois sistemas: listar janelas do AnyDesk, PID,
  título, foco do teclado e fechar sessão. `janelas_x11.py` vem do `x11.py` atual;
  `janelas_win32.py` usa `EnumWindows`, `GetWindowThreadProcessId`, `AttachThreadInput` e
  `SetFocus`.
- **Fechar aba no Windows:** `WM_CLOSE` na janela da sessão, não matar o processo. Um processo do
  AnyDesk pode ter várias sessões.
- **Pacote:** PyInstaller ou Nuitka mais Inno Setup. Sem certificado de assinatura de código, o
  Windows mostra o alerta "Windows protegeu seu computador".

## Riscos (o teste da fase 0 responde)

1. Encaixar janela de outro programa (`SetParent`) não tem suporte oficial da Microsoft.
   Costuma funcionar, mas teclado, foco e redesenho podem falhar.
2. Escala de tela (DPI) diferente entre o app e o AnyDesk deixa a sessão borrada ou do tamanho
   errado.
3. AnyDesk rodando como administrador: o Windows bloqueia o encaixe e o teclado vindo de um
   programa comum. O NaView teria de rodar como administrador também.
4. `anydesk.exe <ID>` pode reaproveitar o processo aberto e abrir a sessão como aba dentro da
   própria janela do AnyDesk. Nesse caso, é preciso uma opção do AnyDesk que abra cada sessão em
   janela própria, ou o encaixe por sessão não funciona.
5. Antivírus podem desconfiar de um programa que mexe nas janelas de outro.

## Fases

| Fase | Entrega | Esforço |
|---|---|---|
| 0 | Teste de viabilidade no Windows (`ferramentas/teste_windows.py`) e relatório | 1–2 dias |
| 1 | Módulo `janelas` com as versões X11 e Windows; app reescrito em Qt (Linux primeiro, para não perder o que funciona) | 2–3 semanas |
| 2 | Jogo no `QWebEngineView` com `QWebChannel` | 2–3 dias |
| 3 | Pacote `.exe`, instalador e testes nos PCs da equipe | 3–5 dias |

A fase 1 só começa se a fase 0 mostrar que encaixe, teclado e escala funcionam.

## Fase 0: como rodar o teste

No PC com Windows:

1. Instalar o Python 3 (python.org) e rodar `py -m pip install PySide6`.
2. Copiar `ferramentas/teste_windows.py` e rodar `py teste_windows.py`.
3. Digitar o ID de um PC de teste (nunca de um cliente) e clicar em Conectar. Esperar a sessão
   abrir, escolher a janela dela na lista e clicar em Encaixar (ou marcar "Encaixar sozinho").
4. Testar e marcar a lista: teclado, atalhos, mouse, redimensionar, nitidez, duas sessões,
   trocar de aba, fechar aba, e tudo de novo com "Forçar foco" ligado e desligado, em cada um dos
   três modos de encaixe.
5. Testar também com o AnyDesk aberto como administrador, se for assim nos PCs da equipe.
6. Clicar em "Salvar relatório" e trazer o `relatorio-windows.txt` e o `naview-piloto-log.txt`.
   Se travar, o `naview-piloto-log.txt` sozinho já mostra onde.

Modos de encaixe do piloto:

- **qt**: `QWindow.fromWinId` + `createWindowContainer` (o planejado para o app).
- **setparent**: `SetParent` direto, com tamanho ajustado por `SetWindowPos(SWP_ASYNCWINDOWPOS)`,
  que não espera o AnyDesk responder.
- **sobrepor**: não prende a janela. Tira a moldura e a mantém por cima da área da aba, logo acima
  do NaView na ordem das janelas. Se os outros travarem, este não junta a fila de teclado e mouse
  dos dois programas.

## Situação

- 15/10/2026: plano feito e script da fase 0 escrito. O script não foi rodado: este computador
  não tem Windows.
- Aguardando o relatório da fase 0, rodado pelo usuário num PC com Windows.
- 15/10/2026: piloto publicado para a equipe testar sem instalar Python: o GitHub Actions monta o
  `NaView-piloto.exe` (PyInstaller e PySide6-Essentials) e a página `/piloto/` do site serve o
  `.zip` (ver [05-landing.md](05-landing.md)). O relatório é salvo ao lado do `.exe` e a pasta
  abre sozinha.
- 16/10/2026: primeiro teste do usuário: o piloto não conectou e a janela travou, sem deixar
  relatório. Causas prováveis: (1) o "Conectar" encaixava a primeira janela nova do AnyDesk, em
  geral o aviso de "conectando" ou de senha, e atrapalhava a conexão; (2) prender a janela de
  outro programa junta a fila de teclado e mouse dos dois, e o NaView congela quando o AnyDesk
  fica ocupado. Correção: Conectar só abre a sessão (encaixe manual ou "Encaixar sozinho" depois
  de a janela ficar 3 s aberta), três modos de encaixe para comparar, registro gravado linha a
  linha em `naview-piloto-log.txt` e um vigia que grava onde o programa parou quando a janela
  fica 3 s sem responder.
- 16/10/2026: **fase 0 aprovada.** O usuário rodou o piloto (versão do dia 15, modo Qt) no
  Windows 11 (26200), escala 100% (96 dpi), NaView como administrador. Passaram todos os itens da
  lista, sem "Forçar foco": sessão sem moldura dentro da aba, teclado, atalhos, mouse,
  redimensionar, nitidez, duas e três sessões ao mesmo tempo, troca de aba, digitar no campo de
  ID, fechar só a aba certa. Sessões ficaram abertas até 50 min sem travar.
  O que o relatório mostrou (os IDs dos PCs ficaram de fora desta spec):
  - Cada `AnyDesk.exe <ID>` abre um **processo próprio** com uma janela só, classe `ad_win#2`,
    em 1 a 2 s. O risco 4 não aconteceu.
  - A janela da sessão é a primeira janela nova; o título vira `<ID com espaços> - AnyDesk`.
  - `WM_CLOSE` fecha a sessão e o processo some; as outras abas continuam (risco de fechar
    tudo não aconteceu).
  - As sessões abertas pelo NaView herdam o administrador dele (`admin=True`); as janelas do
    AnyDesk abertas antes, fora do NaView, rodam sem administrador.
  Ainda em aberto: (a) NaView **sem** administrador; (b) escala de tela 125% ou 150%, comum em
  notebooks (risco 2); (c) antivírus (risco 5); (d) o travamento do primeiro teste, que não se
  repetiu. A versão nova do piloto (modos de encaixe e registro em arquivo) serve para os colegas
  testarem esses pontos.
- 16/10/2026: **fase 1 começou.** Versão Qt do app em `app_qt.py`, ao lado do `app.py` (GTK), que
  continua sendo o usado até a versão Qt chegar ao mesmo nível. Feito e testado no Linux:
  - `plataforma.py`: pastas e AnyDesk de cada sistema. No Linux os caminhos são os mesmos de antes;
    no Windows, `%APPDATA%\NaView` (configuração), `%LOCALAPPDATA%\NaView` (progresso e cache) e
    `%APPDATA%\AnyDesk\user.conf` (contatos, formato ainda a confirmar).
  - `janelas/`: mesma interface nos dois sistemas (`linux.py` usa o `x11.py`; `win32.py` usa a API
    do Windows, com o que o piloto confirmou).
  - `temas_qt.py`: as cores de `temas.py` viram QSS; o fundo da tela inicial e os desenhos são
    pintados à mão, com as mesmas animações (flutuar, balançar, pular, pulsar, navegar, piscar).
  - `aparencia_qt.py`: janela de Aparência.
  - `jogo/tela_qt.py`: o jogo no `QWebEngineView`. Um script injetado cria o mesmo
    `window.webkit.messageHandlers` do WebKit em cima do `QWebChannel`, então `web/jogo.js` não
    mudou. A parte comum às duas telas foi para `jogo/pagina.py`.
  - `jogo/qt.py`: pet do rodapé, sons (`QSoundEffect`) e notificações (D-Bus no Linux, balão da
    bandeja no Windows).
  - Janela sem moldura do sistema, com barra de título própria (arrastar, maximizar, fechar) e
    uma faixa de 6 px em volta para redimensionar. No Linux a janela é transparente (tema vidro
    com desfoque do KWin); no Windows não, porque uma janela transparente não mostra a sessão
    encaixada.
  - Testes: todos os temas e a janela de Aparência renderizados fora da tela; o jogo pela ponte
    (ação "resgatar_diario" respondida); e, com uma janela de teste no lugar do AnyDesk, o app de
    verdade: encaixe, tamanho, teclado na sessão, jogo escondendo e devolvendo a sessão, fechar a
    aba encerrando o processo.
  - Falta: o usuário testar a versão Qt no dia a dia (teclado entre a busca e a sessão, que o KDE
    não deixa testar por script), montar o `.exe` (fase 3) e trocar o atalho do menu para
    `app_qt.py`.
- No Linux, a versão Qt usa os pacotes do Ubuntu (não o `pip`):
  `python3-pyside6.qtwidgets python3-pyside6.qtsvg python3-pyside6.qtwebenginewidgets
  python3-pyside6.qtwebchannel python3-pyside6.qtmultimedia python3-pyside6.qtdbus`.
- 16/10/2026: fase 3 preparada. `.github/workflows/windows.yml` empacota o `app_qt.py` com o
  PyInstaller (PySide6 completo, por causa do QtWebEngine), confere que o `.exe` abre e abre o
  jogo (`--verificar`) e monta `NaView-instalador.exe` com o Inno Setup
  (`ferramentas/instalador.iss`): instala só para o usuário, sem senha de administrador, em
  `%LOCALAPPDATA%\Programs\NaView`, com atalho no menu Iniciar. O instalador passa de 100 MB (limite
  de arquivo do GitHub), então fica como artifact da execução, não no repositório. Falta decidir como
  distribuir para a equipe (ver tarefas).
