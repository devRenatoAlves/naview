# Desempenho: NaView vs AnyDesk puro

Quanto o NaView pesa a mais que usar o AnyDesk direto, sem o app por cima. Números marcados
🟢 **medido** vêm de medição real nesta máquina de teste (Linux); 🟡 **projeção** vêm da estrutura
do código (não cronometrados ainda); 🔴 **aguardando** só dá para medir no computador real de
quem usa (sessão remota de verdade, Windows). Nunca inventamos um número — o que falta medir
aparece marcado como tal.

Reproduza você mesmo: `python3 ferramentas/provisao_uso.py --escenario S1` (e S2/S3/S4, ver
`--help`). Os resultados brutos desta página estão em [`relatorios/`](relatorios/) (JSON).

## Memória (RAM)

| Cenário | NaView | AnyDesk puro | Status |
|---|---|---|---|
| Só o programa, sem sessão aberta (daemon/tray) | — | **3,8 MB** | 🟢 medido |
| App sozinho (GTK3 + WebKit em segundo plano) | ~60–150 MB | — | 🟡 projeção |
| App + 1 sessão ativa | +10–50 MB | ~50–150 MB na sessão | 🟡 projeção |
| App + 1 sessão + **jogo aberto** | +100 MB (WebKit) | — | 🟢 medido o jogo isolado* |
| App + 3 sessões + jogo aberto | ~250 MB | N × engine | 🟡 projeção |

\* O jogo (tela com animações) foi medido isolado, num navegador Chrome headless (não dentro do
NaView): 89–95 MB, mesma animação/código que o app carrega. O WebKitGTK real do NaView tende a
pesar menos que o Chromium usado na medição — então esse número é um **teto**, não o valor exato.

## Processador (CPU)

| Cenário | NaView | AnyDesk puro | Status |
|---|---|---|---|
| Só o programa, idle | — | **~0%** | 🟢 medido |
| App sozinho, jogo fechado | ~0% | — | 🟡 projeção |
| App + sessão ativa | ~0% extra | CPU é do AnyDesk na sessão | 🟡 projeção |
| App + jogo aberto, animado | ~0–40% de 1 núcleo | — | 🟡 projeção (jogo some da CPU quando fechado) |

## Rede

A sessão encaixada **é** a sessão do AnyDesk — o NaView não duplica tráfego, só organiza a janela
em abas. Em repouso, o único tráfego do NaView é checar atualização a cada 6h.

## Disco

| Item | Tamanho | Status |
|---|---|---|
| Programa Linux (fonte + arte + sons + fontes + web + ícones) | **2,4 MB** (222 arquivos) | 🟢 medido |
| Instalador Windows (.exe) | **92,7 MB** | 🟢 medido (enxugado para caber nos 100 MB do GitHub) |
| Repositório completo de desenvolvimento | 1,15 GB | 🟢 medido (não é o que o usuário instala) |

## O que a máquina precisa, na prática

- **1 pessoa, 1 sessão, jogo fechado:** 4 GB RAM, 2 núcleos.
- **Jogo aberto o dia todo:** 8 GB RAM (16 GB se o jogo ficar sempre aberto).
- **2–3 sessões ao mesmo tempo:** 8–16 GB RAM, 4 núcleos se também transferir arquivos.
- **Rede:** a banda é a do AnyDesk; o NaView não soma tráfego próprio.
- **Disco:** ~2 GB livres (programa + atualizações + progresso do jogo).

## O que ainda falta medir

O cenário que representa o uso real da equipe (app aberto, com uma sessão remota de verdade,
no desktop de quem usa) ainda não foi cronometrado — só a estrutura de processos projeta os
números acima. Quem quiser ajudar: `python3 ferramentas/provisao_uso.py --escenario S3 --segundos 60`
com o app aberto e uma sessão ativa, e mandar o `relatorios/provisao_uso_S3_<data>.json` num PR.
O mesmo vale para o Windows (QtWebEngine em vez de WebKitGTK, provavelmente 20–50% mais memória).
