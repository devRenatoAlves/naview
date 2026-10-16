// NaView: página de apresentação. Abas e temas da demonstração, baú de teste e botões de copiar.
(() => {
  "use strict";

  const semMovimento = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---------- Abas da janela de demonstração ----------

  const clientes = ["Padaria Pão Quente", "Clínica Sorriso", "Escritório Lima"];
  const janela = document.querySelector(".janela");
  const abas = [...document.querySelectorAll(".aba")];
  const sessao = document.getElementById("sessao");
  const legenda = document.querySelector(".sessao-legenda");

  function ativarAba(i, focar) {
    abas.forEach((aba, j) => {
      const ativa = i === j;
      aba.setAttribute("aria-selected", String(ativa));
      aba.tabIndex = ativa ? 0 : -1;
    });
    sessao.dataset.cliente = String(i);
    sessao.setAttribute("aria-labelledby", abas[i].id);
    janela.dataset.ativo = String(i);
    legenda.textContent = "Conectado em " + clientes[i];
    if (focar) abas[i].focus();
  }

  abas.forEach((aba, i) => {
    aba.addEventListener("click", () => ativarAba(i, false));
    aba.addEventListener("keydown", (e) => {
      const passo = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
      if (passo) {
        e.preventDefault();
        ativarAba((i + passo + abas.length) % abas.length, true);
      }
    });
  });

  // ---------- Cartas de tema ----------

  const hero = document.querySelector(".hero");
  const cartasTema = [...document.querySelectorAll(".carta-tema")];
  const corDoTopo = { mar: "#0e1638", pixel: "#5ec2ff", hq: "#ffd600", espaco: "#070b1f", neon: "#0d0220", terminal: "#050805" };
  const meta = document.querySelector('meta[name="theme-color"]');

  const caixaTitulo = hero.querySelector(".titulo-caixa");
  const titulo = caixaTitulo.querySelector("h1");

  // Reserva para o título a altura do tema em que ele fica mais alto. Assim, trocar de tema não
  // empurra o texto, os botões nem as cartas. A troca é feita e desfeita antes de a tela ser
  // desenhada, então o visitante não vê nada piscar.
  function reservarTitulo() {
    const atual = hero.dataset.tema;
    hero.classList.add("medindo");
    let maior = 0;
    for (const carta of cartasTema) {
      hero.dataset.tema = carta.dataset.tema;
      maior = Math.max(maior, titulo.getBoundingClientRect().height);
    }
    hero.dataset.tema = atual;
    caixaTitulo.style.minHeight = Math.ceil(maior) + "px";
    hero.offsetHeight; // aplica o tema atual antes de religar as transições
    hero.classList.remove("medindo");
  }

  // Carrega já as fontes dos temas: sem isso, o primeiro clique em cada tema mostra uma fonte
  // provisória e depois pula para a certa.
  const fontesDosTemas = ['16px "Press Start 2P"', '16px "Bangers"', '16px "Orbitron"', '16px "VT323"', '16px "Audiowide"'];
  Promise.all(fontesDosTemas.map((f) => document.fonts.load(f).catch(() => null)))
    .then(() => document.fonts.ready)
    .then(reservarTitulo);
  reservarTitulo();

  let esperaRedimensionar;
  addEventListener("resize", () => {
    clearTimeout(esperaRedimensionar);
    esperaRedimensionar = setTimeout(reservarTitulo, 150);
  });

  cartasTema.forEach((carta) => {
    carta.addEventListener("click", () => {
      const tema = carta.dataset.tema;
      if (hero.dataset.tema === tema) return;
      hero.dataset.tema = tema;
      cartasTema.forEach((c) => c.setAttribute("aria-pressed", String(c === carta)));
      meta.setAttribute("content", corDoTopo[tema]);
      hero.classList.remove("trocando");
      hero.offsetWidth; // reinicia a animação de troca
      hero.classList.add("trocando");
    });
  });
  hero.addEventListener("animationend", () => hero.classList.remove("trocando"));

  // ---------- Baú de demonstração (mesmas chances do app: jogo/catalogo.py) ----------

  const RARIDADES = {
    comum: { nome: "Comum", cor: "#9aa5b1", peso: 70 },
    rara: { nome: "Rara", cor: "#3b82f6", peso: 22 },
    epica: { nome: "Épica", cor: "#a855f7", peso: 6.5 },
    lendaria: { nome: "Lendária", cor: "#f5b81b", peso: 1.2 },
    mitica: { nome: "Mítica", cor: "#ff4d6d", peso: 0.3 },
  };

  const tema = (nome, raridade, descricao, previa) => ({ tipo: "tema", nome, raridade, descricao, previa });
  const comArte = (nome, raridade, descricao, arte) => ({ nome, raridade, descricao, arte });
  const MOLDURA = "arte/icones/sparkle.svg";
  const SOM = "arte/icones/speaker-high.svg";

  const CARTAS = [
    tema("Grafite", "comum", "Escuro, sóbrio e sem distrações.", "linear-gradient(135deg,#1f2125 60%,#7c8cff 60%)"),
    tema("Claro", "comum", "Limpo e luminoso.", "linear-gradient(135deg,#f6f7f9 60%,#2563eb 60%)"),
    tema("Oceano", "rara", "Azul profundo.", "linear-gradient(135deg,#0f2537 60%,#1fa2ff 60%)"),
    tema("Terminal", "epica", "Fósforo verde de monitor antigo.", "linear-gradient(135deg,#050805 60%,#33ff66 60%)"),
    tema("Vidro líquido", "epica", "Transparente com desfoque.", "linear-gradient(135deg,#0b1020 40%,#8be9ff)"),
    tema("Espaço", "lendaria", "Estrelas, planetas e um foguete.", "linear-gradient(135deg,#070b1f 60%,#a78bfa 60%)"),
    tema("Neon 80s", "lendaria", "Pôr do sol retrô e grade neon.", "linear-gradient(135deg,#14052b 60%,#ff2bd6 60%)"),
    tema("Alto-mar", "lendaria", "O veleiro do NaView, farol e ondas.", "linear-gradient(135deg,#111a44 60%,#f59e0b 60%)"),
    tema("Aventura Pixel", "mitica", "Monstrinhos, grama e fonte de videogame.", "linear-gradient(135deg,#8fd3ff 60%,#e8402a 60%)"),
    tema("Heróis HQ", "mitica", "Cores fortes, pontos e explosões.", "linear-gradient(135deg,#ffd600 60%,#e53935 60%)"),
    comArte("Slime", "comum", "Gosmento e muito carinhoso.", "arte/pets/slime.svg"),
    comArte("Pintinho", "comum", "Piu! Acorda cedo todo dia.", "arte/pets/pintinho.svg"),
    comArte("Fantasminha", "rara", "Assusta os bugs dos clientes.", "arte/pets/fantasma.svg"),
    comArte("Gatinho", "rara", "Dorme em cima do teclado.", "arte/pets/gato.svg"),
    comArte("Robô", "epica", "Bip bop. Reinicia o roteador por diversão.", "arte/pets/robo.svg"),
    comArte("Dragãozinho", "lendaria", "Guarda as senhas num tesouro.", "arte/pets/dragao.svg"),
    comArte("Laço", "comum", "Um charme.", "arte/acessorios/laco.svg"),
    comArte("Boné", "comum", "Pronto para a visita técnica.", "arte/acessorios/bone.svg"),
    comArte("Óculos escuros", "rara", "Estilo de quem resolve tudo.", "arte/acessorios/oculos.svg"),
    comArte("Cachecol", "rara", "Para o ar-condicionado do escritório.", "arte/acessorios/cachecol.svg"),
    comArte("Chapéu de mago", "epica", "Para feitiços de suporte remoto.", "arte/acessorios/mago.svg"),
    comArte("Coroa", "lendaria", "Majestade do atendimento.", "arte/acessorios/coroa.svg"),
    comArte("Moldura pontilhada", "comum", "Borda tracejada nos contatos.", MOLDURA),
    comArte("Anel duplo", "rara", "Dois anéis coloridos nos contatos.", MOLDURA),
    comArte("Moldura neon", "epica", "Brilho neon em volta dos avatares.", MOLDURA),
    comArte("Moldura dourada", "lendaria", "Ouro puro em cada contato.", MOLDURA),
    comArte("Bip 8 bits", "comum", "Bip de videogame antigo ao conectar.", SOM),
    comArte("Moedinha", "rara", "Plim! Uma moeda a cada conexão.", SOM),
    comArte("Sino", "epica", "Um sino suave e elegante.", SOM),
    comArte("Fanfarra", "lendaria", "Entrada triunfal em cada cliente.", SOM),
  ];

  function sortear() {
    const total = Object.values(RARIDADES).reduce((s, r) => s + r.peso, 0);
    let x = Math.random() * total;
    let raridade = "comum";
    for (const [chave, r] of Object.entries(RARIDADES)) {
      if ((x -= r.peso) < 0) { raridade = chave; break; }
    }
    const opcoes = CARTAS.filter((c) => c.raridade === raridade);
    return opcoes[Math.floor(Math.random() * opcoes.length)];
  }

  const bau = document.getElementById("bau");
  const cartaGanha = document.getElementById("carta-ganha");
  const cgArte = cartaGanha.querySelector(".cg-arte");
  const cgImg = document.getElementById("cg-img");
  const status = document.getElementById("bau-status");
  const outro = document.getElementById("bau-outro");

  function mostrarCarta(carta) {
    const r = RARIDADES[carta.raridade];
    cartaGanha.style.setProperty("--rar", r.cor);
    cgArte.classList.toggle("tema", carta.tipo === "tema");
    if (carta.tipo === "tema") {
      cgArte.style.setProperty("--previa", carta.previa);
      cgImg.removeAttribute("src");
    } else {
      cgImg.src = carta.arte;
    }
    document.getElementById("cg-rar").textContent = r.nome + (carta.tipo === "tema" ? ", tema" : "");
    document.getElementById("cg-nome").textContent = carta.nome;
    document.getElementById("cg-desc").textContent = carta.descricao;

    bau.hidden = true;
    cartaGanha.hidden = false;
    outro.hidden = false;
    status.textContent = "Você ganhou: " + carta.nome + " (" + r.nome + ").";
    outro.focus();

    const rara = carta.raridade === "lendaria" || carta.raridade === "mitica";
    if (!semMovimento && typeof window.confetti === "function") {
      const cx = cartaGanha.getBoundingClientRect();
      window.confetti({
        particleCount: rara ? 160 : 60,
        spread: rara ? 100 : 60,
        origin: { x: (cx.left + cx.width / 2) / innerWidth, y: (cx.top + cx.height / 3) / innerHeight },
        colors: rara ? [r.cor, "#ffffff", "#f59e0b"] : [r.cor, "#38bdf8", "#6366f1"],
      });
    }
  }

  bau.addEventListener("click", () => {
    const carta = sortear();
    if (semMovimento) { mostrarCarta(carta); return; }
    bau.disabled = true;
    bau.classList.add("tremendo");
    status.textContent = "Abrindo...";
    setTimeout(() => {
      bau.classList.remove("tremendo");
      bau.disabled = false;
      mostrarCarta(carta);
    }, 700);
  });

  outro.addEventListener("click", () => {
    cartaGanha.hidden = true;
    outro.hidden = true;
    bau.hidden = false;
    status.textContent = "";
    bau.focus();
  });

  // ---------- Copiar comandos ----------

  document.querySelectorAll(".copiar").forEach((botao) => {
    botao.addEventListener("click", async () => {
      const texto = botao.previousElementSibling.textContent.trim();
      try {
        await navigator.clipboard.writeText(texto);
        botao.textContent = "Copiado";
      } catch {
        botao.textContent = "Selecione e copie";
      }
      botao.classList.add("copiado");
      setTimeout(() => { botao.textContent = "Copiar"; botao.classList.remove("copiado"); }, 1800);
    });
  });
  // ---------- Linux ou Windows ----------
  //
  // O instalador do Windows não fica no repositório (passa de 100 MB): o GitHub Actions envia para a
  // VPS, junto com windows.json (versão, tamanho e SHA-256). Sem esse arquivo, a página diz "em breve".

  const abasSistema = [document.getElementById("aba-linux"), document.getElementById("aba-windows")];
  const escolherSistema = (aba, focar) => {
    abasSistema.forEach((a) => {
      const sim = a === aba;
      a.setAttribute("aria-selected", String(sim));
      a.tabIndex = sim ? 0 : -1;
      document.getElementById(a.getAttribute("aria-controls")).hidden = !sim;
    });
    if (focar) aba.focus();
  };
  abasSistema.forEach((aba, i) => {
    aba.addEventListener("click", () => escolherSistema(aba, false));
    aba.addEventListener("keydown", (e) => {
      if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
      e.preventDefault();
      escolherSistema(abasSistema[(i + 1) % abasSistema.length], true);
    });
  });

  const noWindows = /Windows/i.test(navigator.userAgent);
  if (noWindows) escolherSistema(abasSistema[1], false);

  fetch("download/windows/windows.json", { cache: "no-store" })
    .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
    .then((info) => {
      document.getElementById("win-em-breve").hidden = true;
      document.getElementById("win-baixar").hidden = false;
      document.getElementById("win-rotulo").textContent = `Baixar o NaView ${info.versao} para Windows`;
      const meta = document.getElementById("win-meta");
      const codigo = document.createElement("code");
      codigo.textContent = info.arquivo;
      meta.replaceChildren("Instalador ", codigo, `, ${info.tamanho}. Para Windows 10 e 11 com o AnyDesk instalado.`);
      document.getElementById("win-sha").textContent = info.sha256;
      if (noWindows) {
        const hero = document.getElementById("hero-baixar");
        hero.href = "download/windows/NaView-instalador.exe";
        hero.querySelector("span").textContent = "Baixar para Windows";
        document.getElementById("hero-nota").textContent = `Versão ${info.versao} para Windows, em teste. Também para Linux.`;
      } else {
        document.getElementById("hero-nota").textContent += " Também para Windows, em teste.";
      }
    })
    .catch(() => {});
})();
