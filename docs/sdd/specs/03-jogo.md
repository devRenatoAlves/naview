# 03: Jogo (fase 1, local)

## Requisitos

- R1. Os atendimentos rendem recompensas **devagar**, porque a demanda de trabalho é alta.
- R2. Coleção de cartas (temas, pets, acessórios, molduras, sons) em raridades.
- R3. Baús com tempo para destravar, baú grátis, recompensa diária e loja.
- R4. Pet no estilo Tamagotchi, que aparece no rodapé da barra de contatos.
- R5. Nível da conta só como comemoração, como conquista de videogame, **sem prêmio**.
- R6. O jogo abre dentro da janela, sem fechar as sessões.
- R7. Toda regra e todo sorteio ficam num único lugar, que pode ir para um servidor.

## Design

- **`jogo/catalogo.py`:** só dados (cartas, raridades, baús, preços, regras do pet).
- **`jogo/progresso.py`:** a classe `Progresso` guarda tudo em SQLite
  (`~/.local/share/naview/progresso.db`) e aplica todas as regras. Os erros de regra são
  `ErroJogo`, e a mensagem vai direto para a tela.
  - Métodos públicos: `estado`, `novidades`, `perfil`, `cartas`, `possui`, `possui_tema`,
    `nivel_carta`, `equipados`, `registrar_atendimento`, `destravar_bau`, `abrir_bau`,
    `abrir_bau_gratis`, `resgatar_diario`, `melhorar_carta`, `equipar`, `comprar_oferta`,
    `comprar_petiscos`, `pet`, `pet_batimento`, `pet_chocar`, `pet_renomear` e `pet_acao`.
  - Para ir ao servidor, basta trocar a classe por outra com esses mesmos métodos que chame a API.
- **`jogo/tela.py`:** `TelaJogo` é um WebKit2 WebView com a página `web/jogo.html`.
  - A página pede ações por `window.webkit.messageHandlers.jogo`.
  - O Python responde por `window.__resposta`, `__iniciar`, `__estado` e `__mostrar`.
  - Fechado há 10 min (`JOGO_LIBERAR_S` em `app.py`), o WebView é destruído para liberar a
    memória do WebKit (100 MB ou mais). Reabrir recria a página.
- **`web/jogo.js`:** a página só desenha. A abertura de baú é animada com GSAP e
  canvas-confetti. O modo de teste usa `window.TESTE` e os endereços `#abrir:N`, `#modal:id`,
  `#pet`.
  - Leveza: um estado novo redesenha só a tela visível; as outras ficam marcadas (`sujas`) e são
    desenhadas ao abrir. O relógio de 1 s não faz nada com a página escondida (`document.hidden`).
  - O pet só é redesenhado (e a animação reiniciada) quando a aparência dele muda; antes ele dava
    um tranco a cada atualização.
  - O brilho das cartas lendárias e míticas anda com `transform` sobre a arte, não com
    `background-position` (que repintava a carta inteira a cada quadro).
- **`jogo/gtk.py`:** pet no rodapé, sons (GStreamer) e notificações (libnotify).
  - `compor_pet` fica em cache (`lru_cache`). O GStreamer carrega 3 s depois de abrir o app, se
    houver som de conexão equipado (`Sons.preparar`).
- **`app.py`:**
  - `registrar_atendimento`: só sessões de 180 s ou mais contam.
  - `batimento` a cada 60 s: avisa quando um baú fica pronto e quando a recompensa diária está
    disponível.
  - Avisa quando a conta sobe de nível.

## Economia atual (números em `jogo/catalogo.py`)

| Item | Valor |
|---|---|
| Cartas | 31: 10 temas, 6 pets, 6 acessórios, 5 molduras, 4 sons |
| Raridades (peso no sorteio) | Comum 70, Rara 22, Épica 6.5, Lendária 1.2, Mítica 0.3 |
| Míticas | Só os temas Aventura Pixel e Heróis HQ |
| Baú de trabalho | 1 a cada **10** atendimentos de 3 min ou mais; sorteio Madeira 50, Prata 35, Ouro 12, Mágico 3 |
| Cartas por baú | Madeira 1, Prata 2, Ouro 3 (mínimo rara), Mágico 5 (mínimo épica), Lendário 3 (mínimo lendária) |
| Tempo para destravar | Madeira 15 min, Prata 1 h, Ouro 3 h, Mágico 8 h; só um baú destrava por vez |
| Espaços de baú | 4 |
| Baú grátis | Madeira, a cada 8 h, acumula 1 |
| Garantia | Lendária depois de 40 baús seguidos sem lendária |
| Recompensa diária (7 dias) | 10 moedas; 1 petisco; 20 moedas; Madeira; 30 moedas + 2 petiscos; Madeira; Prata. Fim de semana não quebra a sequência |
| Loja | 3 ofertas por dia (comum, rara e uma especial); preços 40, 150, 600, 3.000 e 8.000 |
| Atendimento | +3 moedas, +10 XP |
| Melhorar carta | Cópias 2, 4, 8, 16 e moedas 20, 50, 120, 300 (nível 1 a 5) |
| Nível da conta | Nível n exige 100 × n XP; **não dá prêmio** |

### Ritmo medido

Medido por `python3 ferramentas/simular_economia.py`, com a mediana de 20 sorteios em dias
corridos (14/10/2026, já com o tema Alto-mar e os 8 pets novos):

| Marco | 25 atend./dia | 15 atend./dia |
|---|---|---|
| Metade da coleção | 4 | 10 |
| Todas as épicas | 36 | 52 |
| Primeira mítica | 34 | 72 |
| Todas as lendárias | 119 | 212 |
| Coleção completa | 160 (103-218) | 288 (144-394) |
| Conta nível 10 | 19 | 33 |
| Primeiro tema dourado | 88 | 158 |

**Ao mudar qualquer número da economia, rodar o simulador de novo e atualizar esta tabela.**

## Situação

- Pronto: R1 a R7.
- Pets (14/10/2026): slime, pintinho, fantasma, gato, robô e dragão, mais passarinho e Fredinho, o
  pinscher caramelo (comuns), Ronaldo, o salsicha, e corgi (raros), Jigglypuff e Eevee (épicos),
  Pikachu e Gengar (lendários).
- Arte dos pets: pixel art num quadro de 64 x 64 (`PET_LADO`), com 16 linhas livres acima para
  chapéus (`PET_ACIMA`).
  - Pets próprios: camadas vetoriais convertidas em pixels com contorno e sombra em blocos
    (`ferramentas/desenhos_pets.py` e `ferramentas/pixel_vetor.py`), geradas por `gerar_arte.py`.
  - Pokémon: sprites oficiais de Black/White (PokeAPI), baixados por `ferramentas/baixar_sprites.py`.
  - Acessórios: desenhos próprios com uma âncora. `ENCAIXE_PET` guarda os pontos (x, y) de
    topo, olhos e pescoço de cada pet, e `encaixe_acessorio()` devolve posição e tamanho. É usado
    pelo app (`compor_pet`) e pela tela do jogo (`CAT.encaixes`).
  - Pet novo: desenhar (ou baixar), medir os três pontos no quadro e somar em `ENCAIXE_PET`.
  - Tela do pet: cada pixel do desenho vira 4 px (bebê), 4,5 px (jovem) ou 5 px (adulto); o ovo,
    4 px.
- Problemas conhecidos:
  - As moedas sobram com o tempo.
  - O nível da carta só tem efeito nos temas (versão dourada).
- Fase 2, ideias: missões diárias, mais cartas (efeitos, fundos), efeito de nível para todos os
  tipos de carta.
