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
    `comprar_petiscos`, `pet`, `pet_batimento`, `pet_chocar` e `pet_acao`.
  - Para ir ao servidor, basta trocar a classe por outra com esses mesmos métodos que chame a API.
- **`jogo/tela.py`:** `TelaJogo` é um WebKit2 WebView com a página `web/jogo.html`.
  - A página pede ações por `window.webkit.messageHandlers.jogo`.
  - O Python responde por `window.__resposta`, `__iniciar`, `__estado` e `__mostrar`.
  - Fechado há 10 min (`JOGO_LIBERAR_S` em `app.py`), o WebView é destruído para liberar a
    memória do WebKit (100 MB ou mais). Reabrir recria a página.
- **Visual pixel art (22/10/2026, etapa 2 do redesenho):** `web/jogo.css` foi reescrito: contornos em
  degraus feitos com `box-shadow` sem desfoque (cantos recortados), fontes Press Start 2P (títulos e
  botões) e VT323 (texto), paleta de madeira escura, barras em segmentos, animações em `steps()` e
  nada de gradiente suave. Os ícones são pixel art própria 11x11 (`ferramentas/gerar_icones_pixel.py`
  gera `web/icones.js`; os Phosphor ficaram só no GTK). Organização: menu em coluna à esquerda (embaixo
  em janela com menos de 720 px), na tela de Baús os seus baús vêm primeiro e depois o baú grátis e a
  recompensa diária. Falta trocar a arte dos baús, da moeda e dos itens (etapa 3) e dos pets
  (etapa 4).
- **Leveza (22/10/2026):** com o jogo escondido o app chama `window.__pausar(true)` (`TelaJogo.pausar`),
  que congela as animações do CSS e o relógio do GSAP; ao abrir, `pausar(False)`. O GSAP anda a 30 fps
  e o pet em repouso se mexe em poucos passos (`steps()`), em vez de rotação suave com 60 quadros por
  segundo. Na grade da coleção as cartas lendárias/míticas ficam paradas e só animam com o mouse em
  cima. Medido em 8 s: tela do pet de ~3,2 s de CPU para ~1,0 s; página pausada, ~0.
- **Arte dos itens (etapa 3):** baús (5), moeda e petisco em pixel art própria, gerados por
  `ferramentas/gerar_itens_pixel.py` (grade 32x28 com tampa abaulada, tábuas, cintas e cantoneiras de
  metal, fecho com gema ou fechadura; contorno automático e uma paleta por baú; o `gerar_arte.py` não
  gera mais esses arquivos). Cada baú tem também `<tipo>_aberto.svg` (tampa levantada e brilho dentro),
  usado na abertura: o baú treme de lado, troca para o aberto e some, sem girar nem desfocar.
- **Pets (etapa 4):** os pets próprios continuam desenhados em `ferramentas/desenhos_pets.py`, agora com
  contorno seletivo (a borda acompanha a cor de cada parte, em `pixel_vetor.montar`) e olhos grandes
  com brilho duplo. `gerar_arte.py` gera também `arte/pets/<pet>_pisca|feliz|triste.svg`
  (`pixel_vetor.expressao`): a página usa a cara do humor do pet (dormindo = olhos fechados, feliz =
  olhos em arco, triste = lágrima) e ele pisca a cada 3 a 6,5 s com a tela do pet à vista. Só os pets
  com olhos de grade (`PETS_COM_EXPRESSAO` no catálogo: hoje só Fredinho e Ronaldo, depois da
  reformulação de 22/10/2026); os demais pets ficam com um desenho só.
- **Reformulação dos pets (22/10/2026):** ficaram só Fredinho, Ronaldo e os 4 Pokémon (Pikachu, Eevee,
  Jigglypuff, Gengar). Saíram corgi, passarinho, pintinho, fantasma e robô. Os outros pets vieram das
  imagens do usuário (copiadas para `ferramentas/originais_pets/`) e são gerados por
  `ferramentas/importar_pets.py`:
  - GIFs de 8 quadros (130 ms cada): **gato** (gatinho preto), **Jonatas**, **astronauta** e **dragao**
    (serpente de gelo, 128 x 128, 64 x 114 depois de cortar a transparência e 1 coluna de cada lado).
    O quadro 0 também é `arte/pets/<pet>.svg` (rodapé, cartas); a página troca entre `<pet>_q0..q7.png`
    (PNG decodifica bem mais leve que SVG a cada troca: CPU em 8 s da tela do pet, medido fora do app:
    slime parado ~1,25 s, dragão ~1,3 s, gato e Jonatas ~1,7 s, ou seja, +5% de um núcleo só com a tela do
    pet aberta; com SVG o dragão gastava ~1,5 s). Todos os quadros
    usam o mesmo deslocamento no quadro de 64 x 64 (caixa que cobre todos), para o pet não tremer.
  - PNGs parados em células (um pixel por célula, moldura rosa e fundo branco de fora descartados):
    **galinha** (células de 10 px, 54 x 66) e **slime** (células de 18 px, 46 x 38). Não têm caras
    por humor; usam só o balanço da página.
  - Os ids `pet-slime`, `pet-gato` e `pet-dragao` foram mantidos (arte nova), para não perder cartas e
    pets já salvos. Novos: `pet-galinha`, `pet-jonatas`, `pet-astronauta`. O ovo agora choca slime ou
    galinha.
  - Raridades: Comum: slime, galinha. Rara: gato, Ronaldo. Épica: astronauta, Jigglypuff, Eevee,
    Jonatas. Lendária: Fredinho, serpente de gelo, Pikachu, Gengar.
  - **Animação:** a página troca o quadro do `<img>` no ritmo do GIF (`QUADRO_MS`) só com a tela do pet à
    vista, o pet acordado e o jogo sem pausa (sem timer nenhum fora disso, `agendarQuadros` em
    `jogo.js`). O acessório acompanha a cabeça com `QUADROS` (deslocamento x, y da cabeça em cada
    quadro, medido pelo topo do desenho). Rodapé do app (GTK e Qt) usa o quadro 0 parado.
  - **Dragão:** 114 de altura. `ALTURA_EXTRA` = 50 e `ACIMA_PET` = 64 (espaço livre de cima só dele,
    `acima_de()`); `ESCALA_PAGINA` = 0,5 deixa o pixel dele com metade do tamanho na página (reduzir o
    desenho a 57 px de altura apagava o rosto). Acessórios ficam no tamanho normal.
  - **Acessórios:** `ENCAIXE_PET` refeito para os novos; `AJUSTE_ACESSORIO` com óculos de perfil e
    cachecol estreito para galinha e dragão (de perfil). Conferido numa folha de contato de
    todos os pets x 6 acessórios (`jogo.gtk.compor_pet`) e na página.
  - **Conferência de encaixe (22/10/2026):** renderizadas a coleção filtrada por Pet, o modal de cada carta,
    o guarda-roupa (Espécies), o palco com os 12 pets de óculos e o rodapé da barra lateral (`pet_rodape`, 12
    pets x 5 acessórios). Correções: nas cartas e nos botões o pet agora é recortado no próprio desenho
    (`pagina.caixa_do_pet` + `petMini` em `jogo.js`) e enche a área, em vez de aparecer pequeno no quadro de
    64; a serpente de gelo vazava do botão do guarda-roupa; na serpente os óculos cobriam o focinho e o
    cachecol ficava fora do pescoço (`ENCAIXE_PET` e `AJUSTE_ACESSORIO` refeitos). Os óculos de perfil
    (lente de 11 x 8) ainda eram grandes para a cabeça de ~21 px: a serpente ganhou `oculos_lado_mini`
    (lente 7 x 6, haste para trás), centrado no olho (21, -26) e conferido a 14x e na página.
  - **Migração (`Progresso._migrar_pets`):** apaga do banco as cartas que saíram do catálogo e, se o
    pet atual era de uma espécie removida, ele vira o Slime (mantém nome, XP e acessório).
  - A arte é de terceiros (uso interno, como os Pokémon e o modelo do Fredinho): não vai para a
    página de apresentação; a lista de pets da página foi retirada.
- **Pincel de pixels (22/10/2026):** `pixel_vetor.Tela` desenha formas pixel a pixel (elipse, polígono,
  retângulo) com luz no alto à esquerda, sombra embaixo à direita e contorno na cor de cada parte, sem
  a suavização do caminho vetorial. Fredinho (`pinscher`), pintinho e passarinho foram refeitos com
  ele (pintinho e passarinho). Os encaixes dos acessórios foram recalculados em `ENCAIXE_PET`.
- **Fredinho (22/10/2026):** o usuário escolheu um sprite de chihuahua como modelo ("sprite exemplo.jpg",
  um esquema de ponto cruz em que cada ponto é um pixel) para ser copiado quase igual, só com a cor do
  cachorro real. O desenho foi extraído célula a célula (57 x 71 pixels, bordas e olhos incluídos) e
  recolorido: corpo caramelo em 3 tons, sobrancelhas, focinho e peito cremes, pernas caramelo claro,
  patinhas cremes, orelhas rosadas por dentro e contorno marrom-escuro. O resultado está como texto em
  `desenhos_pets.FREDINHO` (a imagem do modelo não precisa ficar no repositório). As caras pisca, feliz
  e triste trocam só as células dos olhos (`Grade.expressoes`).
  - Como o desenho tem 71 de altura e o quadro dos pets 64, o SVG ganha 7 linhas em cima (viewBox com
    y negativo) e o catálogo guarda `ALTURA_EXTRA = {"pinscher": 7}`; a página, o GTK e o Qt posicionam
    o pet com esse valor.
  - O modelo é arte de terceiros: uso interno da equipe, como os Pokémon (D18); não vai para a página
    pública nem para o instalador sem decisão do usuário.
- **Encaixe dos acessórios (22/10/2026):** o encaixe padrão (`ENCAIXE_PET` + `ENCAIXE_ACESSORIO`) serve
  para pets de frente. Para pets de lado ou de pescoço estreito há `AJUSTE_ACESSORIO` no catálogo:
  (pet, acessório) -> (arquivo, ponto no quadro, âncora, tamanho). `encaixe_acessorio()` devolve também o
  `arquivo`, que a página, o GTK e o Qt usam no lugar do nome do acessório. Variantes em
  `arte/acessorios/`: `oculos_lado` (uma lente e a haste, para quem olha à esquerda), `oculos_lado_dir`
  (espelhado, para quem olha à direita) e `cachecol_estreito` (18 px em vez de 30). Usadas em Fredinho
  (óculos largos com lentes a 15 px, cachecol estreito sob o queixo), Ronaldo e passarinho (óculos de
  perfil e cachecol estreito). Os chapéus de Ronaldo e passarinho foram baixados 2 px para assentar.
  Conferidos os 6 acessórios nos 14 pets por folha de contato (`jogo.gtk.compor_pet` em 3x e 8x) e na
  página; os demais pets (de frente) já estavam encaixados. Ao refazer um pet, recalcular o encaixe.
- **Ronaldo (22/10/2026):** mesmo método do Fredinho, mas o modelo ("SPRITE EXEMPLO.png", salsicha de
  lado com orelha caída e cauda levantada) já era um PNG limpo de 16 cores, então a grade (46 x 48) foi lida
  exatamente (células de 18 px, sem k-means). Recolorido a partir das 4 fotos do cachorro real: corpo
  marrom-avermelhado uniforme (o modelo era preto e fogo: o preto virou o pelo base e o fogo virou luz do
  mesmo pelo), orelhas marrom-chocolate mais escuras (separadas por posição, x 20 a 31 e y 5 a 23), nariz
  preto, olhos escuros. Texto em `desenhos_pets.RONALDO`; caras pisca, feliz e triste em
  `Grade.expressoes`; `salsicha` entrou em `PETS_COM_EXPRESSAO` e os encaixes foram recalculados.
  Mesma regra de direitos do Fredinho: o modelo é de terceiros, uso interno.
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
  - Pet do rodapé (`pet_rodape`): recorta o espaço vazio do quadro e amplia o desenho até caber em
    72 x 56 px (no máximo 1,7 vez), centralizado, com 8 px livres em cima para a animação. Sem isso,
    os pets menores (slime, salsicha, Jigglypuff) ficavam pequenos e encostados embaixo.
  - `compor_pet` e `pet_rodape` ficam em cache (`lru_cache`). O GStreamer carrega 3 s depois de abrir o app, se
    houver som de conexão equipado (`Sons.preparar`).
- **`app.py`:**
  - `registrar_atendimento`: só sessões de 180 s ou mais contam. **Anti-trapaça (23/10/2026):** o mesmo ID
    (espaços ignorados) conta no máximo 2 vezes em 24 h, janela deslizante (`ATENDIMENTOS_MAX_POR_ID`,
    `ATENDIMENTOS_JANELA_H`); a 3ª sessão devolve `{"limitado": True}` e o app avisa que não conta. IDs
    diferentes não têm limite. Sessão sem ID conhecido (`cid` None) conta sempre. Sessão recusada não é
    gravada, então não estende a janela. O limite vale só no cliente local: a validação real vem com o
    servidor (D14).
  - `batimento` a cada 60 s: avisa quando um baú fica pronto e quando a recompensa diária está
    disponível.
  - Avisa quando a conta sobe de nível.

## Economia atual (números em `jogo/catalogo.py`)

| Item | Valor |
|---|---|
| Cartas | 39: 12 temas, 12 pets, 6 acessórios, 5 molduras, 4 sons |
| Raridades (peso no sorteio) | Comum 70, Rara 22, Épica 6.5, Lendária 1.2, Mítica 0.3 |
| Míticas | Só os temas Aventura Pixel, Heróis HQ e Mangá Noir |
| Baú de trabalho | 1 a cada **10** atendimentos de 3 min ou mais (mesmo ID: no máximo 2 em 24 h); sorteio Madeira 50, Prata 35, Ouro 12, Mágico 3 |
| Cartas por baú | Madeira 1, Prata 2, Ouro 3 (mínimo rara), Mágico 5 (mínimo épica), Lendário 3 (mínimo lendária) |
| Tempo para destravar | Madeira 15 min, Prata 1 h, Ouro 3 h, Mágico 8 h; só um baú destrava por vez |
| Espaços de baú | 4 |
| Baú grátis | Madeira, a cada 8 h, acumula 1 |
| Garantia | Lendária depois de 40 baús seguidos sem lendária |
| Recompensa diária (7 dias) | 10 moedas; 1 petisco; 20 moedas; Madeira; 30 moedas + 2 petiscos; Madeira; Prata. Fim de semana não quebra a sequência |
- **Loja**: 3 ofertas por dia (comum, rara e uma especial), sorteadas aleatoriamente para cada
  usuário, com a ordem embaralhada a cada renovação; preços 40, 150, 600, 3.000 e 8.000.
| Atendimento | +3 moedas, +10 XP |
| Melhorar carta | Cópias 2, 4, 8, 16 e moedas 20, 50, 120, 300 (nível 1 a 5) |
| Nível da conta | Nível n exige 100 × n XP; **não dá prêmio** |

### Ritmo medido

Medido por `python3 ferramentas/simular_economia.py`, com a mediana de 20 sorteios em dias
corridos (23/10/2026, com 39 cartas, Fredinho lendário, Jonatas épico e loja aleatória; a rodada
completa leva cerca de 2 min, porque o simulador usa um banco sem espera de gravação em disco):

| Marco | 25 atend./dia | 15 atend./dia |
|---|---|---|
| Metade da coleção | 8 | 15 |
| Todas as épicas | 38 | 58 |
| Primeira mítica | 31 | 87 |
| Todas as lendárias | 139 (109-200) | 208 (152-354) |
| Coleção completa | 195 (148-283) | 291 (194-362; só 16 de 20 chegaram em 400 dias) |
| Conta nível 10 | 19 | 33 |
| Primeiro tema dourado | 74 | 124 |

Comparada com a de 22/10/2026 (183 e 297 dias para a coleção completa), o ritmo quase não mudou: a
troca de raridade de dois pets e a loja aleatória pesam pouco perto da carta mítica (0,3% de chance),
que domina o tempo até completar. O ritmo continua lento. O limite de 2 atendimentos por ID em 24 h
não entra na simulação, que usa um ID diferente por atendimento.

**Ao mudar qualquer número da economia, rodar o simulador de novo e atualizar esta tabela.**

## Situação

- Pronto: R1 a R7.
- Pets (reformulados em 22/10/2026): slime, galinha (comuns), gato e Ronaldo (raros),
  astronauta, Jigglypuff, Eevee e Jonatas (épicos), serpente de gelo, Pikachu, Gengar e
  Fredinho (lendário).
- Arte dos pets: pixel art num quadro de 64 x 64 (`PET_LADO`), com 16 linhas livres acima para
  chapéus (`PET_ACIMA`).
  - Pets próprios: camadas vetoriais convertidas em pixels com contorno e sombra em blocos
    (`ferramentas/desenhos_pets.py` e `ferramentas/pixel_vetor.py`), geradas por `gerar_arte.py`.
  - Pokémon: sprites oficiais de Black/White (PokeAPI), baixados por `ferramentas/baixar_sprites.py`.
  - Acessórios: desenhados pixel a pixel em texto (um caractere por pixel, em
    `ferramentas/desenhos_pets.py`, lido por `de_mapa`), com contorno, luz e sombra; o cachecol é
    montado por código. Cada um tem uma âncora. `ENCAIXE_PET` guarda os pontos (x, y) de
    topo, olhos e pescoço de cada pet, e `encaixe_acessorio()` devolve posição e tamanho. É usado
    pelo app (`compor_pet`) e pela tela do jogo (`CAT.encaixes`).
  - Pet novo: desenhar (ou baixar), medir os três pontos no quadro e somar em `ENCAIXE_PET`.
  - Tela do pet: cada pixel do desenho vira 4 px (bebê), 4,5 px (jovem) ou 5 px (adulto); o ovo,
    4 px.
- Petisco (biscoito com gotas, pixel art 16 x 16), moeda (com estrela e borda em relevo) e baús
  (tábuas, cantoneiras, rebites e fechadura) são gerados por `ferramentas/gerar_arte.py`.
- Problemas conhecidos:
  - As moedas sobram com o tempo.
  - O nível da carta só tem efeito nos temas (versão dourada).
- Fase 2, ideias: missões diárias, mais cartas (efeitos, fundos), efeito de nível para todos os
  tipos de carta.
