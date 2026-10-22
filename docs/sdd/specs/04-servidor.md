# 04: Servidor da equipe (em planejamento)

## Objetivo

Cada colaborador tem uma conta. O progresso fica no servidor, então nada se perde ao trocar ou
formatar o computador. Com isso, a equipe passa a ter **ranking e prêmios reais**.

## Requisitos

- R1. Login leve: usuário e senha, uma vez por computador. O app lembra o login (token).
- R2. As contas são criadas pelo administrador (o usuário). Não existe cadastro aberto.
- R3. Ao entrar em outro computador, a conta e o histórico vêm do servidor.
- R4. **Anti-trapaça:** como há prêmios reais, as regras e os sorteios rodam **no servidor**. O
  computador do colaborador só mostra o jogo e pede ações.
- R5. Os atendimentos são **conferidos pela API REST do AnyDesk**: sessão falsa ou curta não
  conta. Se a API não estiver disponível, usar o plano B.
- R6. Sem internet, o app de abas funciona normalmente. Os atendimentos ficam numa fila e são
  enviados depois. Abrir baú e comprar exigem conexão.
- R7. O progresso local atual do usuário é migrado para a conta dele.
- R8. Ranking da equipe e painel do administrador (contas, prêmios, relatório de atendimentos).
- R9. ~10 usuários. Precisa ser simples de manter.

## Design proposto

- **Servidor em Python, reaproveitando `jogo/progresso.py`:**
  - Um `Progresso` por colaborador. As regras não são reescritas.
  - Um banco SQLite no servidor basta para 10 pessoas.
  - API HTTP com JSON. O framework ainda vai ser escolhido; a ideia é algo leve, como FastAPI, ou
    só a biblioteca padrão.
- **Cliente:** uma classe `ProgressoRemoto` com os mesmos métodos públicos de `Progresso` (ver
  [03-jogo.md](03-jogo.md)). `app.py` e `jogo/tela.py` quase não mudam.
- **Senhas:** guardadas como hash forte (ex.: bcrypt ou scrypt). O token fica salvo no
  computador do colaborador.
- **HTTPS:** obrigatório na internet. Com domínio, usar Caddy ou nginx com Let's Encrypt. Só com
  IP, é preciso decidir outro caminho.
- **Conferência de atendimentos:** o servidor consulta a API do AnyDesk (lista de sessões com
  duração) e só credita as sessões confirmadas.
- **Plano B (sem API):** limite diário de atendimentos que contam e relatório para o
  administrador conferir.

## Hospedagem

- VPS do usuário, acessada por SSH a partir deste computador. Existe o arquivo `~/.ssh/minhavps`,
  provavelmente a chave. Não há `~/.ssh/config`.
- **Regra:** antes de qualquer comando que mude algo na VPS, explicar e pedir confirmação.
  Senhas, da VPS ou do AnyDesk, nunca passam pelo chat: vão direto para um arquivo de
  configuração na VPS.

## Pendências (aguardando o usuário)

- [ ] Plano do AnyDesk: o usuário respondeu "Advanced ou Ultimate" e está confirmando. A API REST
      depende do plano.
- [ ] Dados da VPS: endereço (IP ou domínio), usuário do SSH, sistema (ex.: Ubuntu ou Debian), o
      que já roda nela (site, Docker, nginx).
- [ ] Domínio para HTTPS: existe ou não?
- [ ] Prêmios reais: quais são e com que critério (posição no ranking, metas).

## Fases

1. Servidor e login: contas, progresso e sorteios no servidor; o app pede login.
2. Migração do progresso local do usuário.
3. Conferência de atendimentos pela API do AnyDesk.
4. Ranking, prêmios e painel do administrador.

## Perfil dos colegas (ideia de 22/10/2026, ainda não iniciada)

Cada colaborador pode ver o inventário dos outros, só leitura, no estilo do perfil de amigos da
Steam (cartas, pet, nível, conquistas). Depende das fases 1 e 2 acima: sem o progresso no servidor
não há de onde ler.

### Requisitos

- R10. Aba "Equipe" no jogo, com a lista de colegas (nome, nível, quantidade de cartas).
- R11. Clicar num colega abre o perfil dele em modo só leitura: coleção, pet e conquistas.
- R12. O servidor devolve só dados públicos. Nunca token, senha nem histórico de atendimentos.
- R13. Cada pessoa pode esconder o próprio inventário (padrão: visível para a equipe).
- R14. Leve (regra do CLAUDE.md): chamadas só em thread, com tempo limite curto; nada de timer
  contínuo; lista buscada ao abrir a aba e guardada por alguns minutos; o servidor manda só IDs de
  cartas (a arte já está no pacote, em `arte/`); sem servidor, o app funciona normalmente e a aba
  mostra "indisponível".

### Design proposto

- Endpoints de leitura: `GET /equipe` (lista) e `GET /equipe/<usuario>` (perfil público).
- Tela nova em `jogo/` com a mesma aparência das listas e cartas existentes (sem efeito caro).
- Ranking e "quem tem a carta X" reaproveitam os mesmos dados.
- Troca ou presente de cartas entre colegas: fora do primeiro corte; exige regras contra fraude.

### Ordem

1. Servidor, login e progresso no servidor (fases 1 e 2).
2. Endpoint e tela de perfil, só leitura.
3. Ranking.
4. Troca, se o usuário quiser.

### Decisões pendentes (do usuário)

- Privacidade: inventário sempre visível ou opcional? (recomendado: visível, com opção de esconder)
- O que mostrar: só cartas e pet, ou também atendimentos e estatísticas?
- Troca entre pessoas: só ver, ou também trocar?
- Dados da VPS (ver "Pendências" acima).

### Peso

Baixo: pedidos HTTP curtos (poucos KB de JSON) em thread; SQLite com ~10 pessoas é desprezível na
VPS. Medir antes de entregar (CPU/memória com a aba aberta, fechada e o app parado), como em
`testes.md`.
