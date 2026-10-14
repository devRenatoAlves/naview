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
- [x] Barra de contatos retrátil
- [x] Corrigir a tela do jogo cortada quando o app abre com a barra lateral aberta
- [x] Atalho no menu do KDE (`.desktop`) e ícone próprio
- [x] Revisão da interface: ícones, cartão de conexão rápida, avatares, avisos, abas
- [ ] Testar com sessões reais: teclado, atalhos, tela cheia, transferência de arquivos
- [ ] Conferir o formato do título da janela de sessão (nome do computador) em sessão real
- [ ] Atalhos para trocar de aba (Ctrl+Tab, Ctrl+1..9)

## Temas ([spec](specs/02-temas.md))

- [x] Temas completos (fonte, arte e animações) e vidro líquido
- [x] Temas bloqueados na Aparência para quem não tem a carta

## Jogo ([spec](specs/03-jogo.md))

- [x] Fase 1: cartas, baús, recompensa diária, loja e pet Tamagotchi (local)
- [x] Ritmo lento de recompensas: coleção completa em ~4 a 8 meses
- [x] Nível da conta só como comemoração (as recompensas de nível foram removidas)
- [x] Simulador da economia (`ferramentas/simular_economia.py`)
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
- [~] Definir como o código chega ao Coolify (repositório git ou envio direto) e o domínio
- [ ] Publicar na VPS pelo Coolify (domínio e HTTPS)
