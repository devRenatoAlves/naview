# 06: NaView no Windows (em planejamento)

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
3. Digitar o ID de um PC de teste (nunca de um cliente) e clicar em Conectar. Também dá para
   encaixar uma janela já aberta pela lista.
4. Testar e marcar a lista: teclado, atalhos, mouse, redimensionar, nitidez, duas sessões,
   trocar de aba, fechar aba, e tudo de novo com "Forçar foco" ligado e desligado.
5. Testar também com o AnyDesk aberto como administrador, se for assim nos PCs da equipe.
6. Clicar em "Salvar relatório" e trazer o `relatorio-windows.txt`.

## Situação

- 15/10/2026: plano feito e script da fase 0 escrito. O script não foi rodado: este computador
  não tem Windows.
- Aguardando o relatório da fase 0, rodado pelo usuário num PC com Windows.
- 15/10/2026: piloto publicado para a equipe testar sem instalar Python: o GitHub Actions monta o
  `NaView-piloto.exe` (PyInstaller e PySide6-Essentials) e a página `/piloto/` do site serve o
  `.zip` (ver [05-landing.md](05-landing.md)). O relatório é salvo ao lado do `.exe` e a pasta
  abre sozinha.
