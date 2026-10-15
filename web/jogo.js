"use strict";
/* Tela do jogo: baús, coleção de cartas, pet e loja.
 * Quem guarda o progresso e decide os sorteios é o Python (jogo/progresso.py); esta página só
 * pede ações pela ponte e desenha o estado que volta. */

const $ = (s, raiz = document) => raiz.querySelector(s);
const $$ = (s, raiz = document) => [...raiz.querySelectorAll(s)];
function el(tag, classe = "", html = "") {
  const e = document.createElement(tag);
  if (classe) e.className = classe;
  if (html) e.innerHTML = html;
  return e;
}

let CAT = null;          // catálogo (cartas, raridades, baús...) enviado pelo Python
let EST = null;          // estado atual do jogador
let recebidoEm = 0;      // quando o estado chegou (para os relógios andarem sozinhos)
let filtro = "todas";
let animando = false;
let somLigado = true;
try { somLigado = localStorage.getItem("sons") !== "0"; } catch (e) { /* sem armazenamento */ }

const ARTE = "../arte/";
// Troca <i data-ic="nome"> pelo desenho do ícone (Phosphor, ver icones.js).
$$("[data-ic]").forEach((n) => { n.innerHTML = ic(n.dataset.ic); });
const escapar = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const SONS = "../sons/";
const confete = window.confetti ? confetti.create($("#confete"), { resize: true }) : () => {};

/* ---------------- ponte com o Python ---------------- */

const pendentes = new Map();
let proximoId = 1;

function chamar(acao, dados = {}) {
  if (!window.webkit || !window.webkit.messageHandlers || !window.webkit.messageHandlers.jogo) {
    return testeResponder(acao, dados);
  }
  return new Promise((ok, falha) => {
    const id = proximoId++;
    pendentes.set(id, { ok, falha });
    window.webkit.messageHandlers.jogo.postMessage(JSON.stringify({ id, acao, dados }));
  });
}

window.__resposta = (id, sucesso, valor, estado) => {
  const p = pendentes.get(id);
  pendentes.delete(id);
  if (estado) aplicarEstado(estado);
  if (!p) return;
  if (sucesso) p.ok(valor); else p.falha(new Error(valor));
};
window.__iniciar = (catalogo, estado, tela) => {
  CAT = catalogo;
  montarFiltros();
  aplicarEstado(estado);
  if (tela) irPara(tela);
};
window.__estado = (estado) => aplicarEstado(estado);
window.__mostrar = (tela) => irPara(tela);

async function acao(nome, dados) {
  try {
    return await chamar(nome, dados);
  } catch (e) {
    avisar(e.message);
    tocar("clique");
    return null;
  }
}

/* ---------------- utilidades ---------------- */

function tocar(nome) {
  if (!somLigado) return;
  try { const a = new Audio(SONS + nome + ".wav"); a.volume = 0.6; a.play().catch(() => {}); } catch (e) { /* sem som */ }
}

let avisoTimer = null;
function avisar(texto, icone = null) {
  const a = $("#aviso");
  a.innerHTML = (icone ? ic(icone) + " " : "") + escapar(texto);
  a.classList.add("on");
  clearTimeout(avisoTimer);
  avisoTimer = setTimeout(() => a.classList.remove("on"), 2600);
}

function tempo(s) {
  s = Math.max(0, Math.round(s));
  if (s >= 3600) return `${Math.floor(s / 3600)}h ${String(Math.floor((s % 3600) / 60)).padStart(2, "0")}min`;
  if (s >= 60) return `${Math.floor(s / 60)}min ${String(s % 60).padStart(2, "0")}s`;
  return `${s}s`;
}
const passou = () => (Date.now() - recebidoEm) / 1000;
function duracao(min) { return min >= 60 ? `${min / 60}h` : `${min}min`; }
const moedaImg = `<img class="moeda-inline" src="${ARTE}jogo/moeda.svg" alt="">`;

function carta(id) { return CAT.cartas_por_id[id]; }
function minha(id) { return EST.cartas[id]; }
function precisa(nivel) { return nivel > 0 && nivel < CAT.nivel_max ? CAT.copias_por_nivel[nivel - 1] : null; }
function emUso(c) {
  const eq = EST.equipados;
  switch (c.tipo) {
    case "tema": return EST.tema === c.alvo;
    case "moldura": return eq.moldura === c.alvo;
    case "som": return eq.som === c.alvo;
    case "pet": return EST.pet.especie === c.alvo;
    case "acessorio": return EST.pet.acessorio === c.alvo;
  }
  return false;
}
function podeMelhorar(id) {
  const m = minha(id);
  if (!m) return false;
  const p = precisa(m.nivel);
  return p !== null && m.copias >= p;
}

/* ---------------- navegação ---------------- */

function irPara(tela) {
  $$(".tela").forEach((t) => t.classList.toggle("ativa", t.id === "tela-" + tela));
  $$(".menu-bt").forEach((b) => b.classList.toggle("ativo", b.dataset.tela === tela));
  desenharTela(tela);
  if (tela === "pet") animarPetParado();
}

// Só a tela visível é redesenhada quando o estado muda; as outras ficam marcadas e são
// desenhadas quando a pessoa for até elas.
const DESENHAR = { baus: () => desenharBaus(), colecao: () => desenharColecao(),
                   pet: () => desenharPet(), loja: () => desenharLoja() };
let sujas = new Set();
function telaAtiva() {
  const t = $(".tela.ativa");
  return t ? t.id.replace("tela-", "") : null;
}
function desenharTela(tela) {
  if (!EST || !sujas.has(tela)) return;
  sujas.delete(tela);
  DESENHAR[tela]();
}
$$(".menu-bt").forEach((b) => b.addEventListener("click", () => { tocar("clique"); irPara(b.dataset.tela); }));
$("#bt-fechar").addEventListener("click", () => chamar("fechar").catch(() => {}));
$("#bt-som").addEventListener("click", () => {
  somLigado = !somLigado;
  try { localStorage.setItem("sons", somLigado ? "1" : "0"); } catch (e) { /* ok */ }
  desenharTopo();
});

/* ---------------- estado ---------------- */

function aplicarEstado(e) {
  // Subir de nível não dá prêmio: é só comemoração, como conquista de videogame.
  const subiu = EST && e.perfil.nivel > EST.perfil.nivel;
  EST = e;
  if (subiu) {
    tocar("fanfarra");
    confete({ particleCount: 120, spread: 90, origin: { y: 0.2 } });
    avisar(`Você chegou ao nível ${e.perfil.nivel}!`, "star");
  }
  recebidoEm = Date.now();
  desenharTopo();
  desenharPontos();
  sujas = new Set(Object.keys(DESENHAR));
  desenharTela(telaAtiva());
}

// Relógios andam sozinhos; quando algo fica pronto, pede o estado de novo ao Python.
// Com o jogo escondido (document.hidden) não faz nada: o app atualiza o estado ao reabrir.
setInterval(() => {
  if (!EST || animando || document.hidden) return;
  const pronto = EST.baus.some((b) => b && b.situacao === "destravando" && b.falta_s - passou() <= 0)
    || (EST.gratis.proximo_s !== null && EST.gratis.proximo_s - passou() <= 0);
  if (pronto) { chamar("estado").then(aplicarEstado).catch(() => {}); return; }
  atualizarRelogios();
}, 1000);

function atualizarRelogios() {
  $$("[data-falta]").forEach((n) => { n.textContent = tempo(Number(n.dataset.falta) - passou()); });
}

function desenharTopo() {
  const p = EST.perfil;
  $("#nivel").textContent = p.nivel;
  $("#nivel-texto").textContent = p.nivel;
  $("#xp-barra").style.width = `${(100 * p.xp_no_nivel) / p.xp_proximo}%`;
  $("#xp-texto").textContent = `${p.xp_no_nivel}/${p.xp_proximo} XP`;
  $("#moedas").textContent = p.moedas;
  $("#petiscos").textContent = p.petiscos;
  $("#bt-som").innerHTML = ic(somLigado ? "speaker-high" : "speaker-slash");
}

function desenharPontos() {
  const prontos = EST.baus.filter((b) => b && b.situacao === "pronto").length;
  const baus = prontos + EST.gratis.qtd + (EST.diario.disponivel ? 1 : 0);
  const melhorar = Object.keys(EST.cartas).filter(podeMelhorar).length;
  const pet = !EST.pet.chocado || EST.pet.humor === "triste" ? "!" : "";
  for (const [id, valor] of [["#ponto-baus", baus], ["#ponto-colecao", melhorar], ["#ponto-pet", pet]]) {
    $(id).textContent = valor || "";
    $(id).classList.toggle("on", Boolean(valor));
  }
}

/* ---------------- baús ---------------- */

function desenharBaus() {
  const g = EST.gratis;
  $("#gratis-info").innerHTML = g.qtd > 0
    ? `<b>${g.qtd}/${g.max}</b> disponíve${g.qtd > 1 ? "is" : "l"}`
      + (g.proximo_s !== null ? ` · próximo em <span data-falta="${g.proximo_s}">${tempo(g.proximo_s)}</span>` : "")
    : `Próximo em <span data-falta="${g.proximo_s}">${tempo(g.proximo_s)}</span>`;
  $("#bt-gratis").disabled = g.qtd <= 0;

  const d = EST.diario;
  $("#diario-seq").innerHTML = d.sequencia
    ? `· ${d.sequencia} dia${d.sequencia > 1 ? "s" : ""} seguido${d.sequencia > 1 ? "s" : ""} ${ic("fire", "ic-fogo")}` : "";
  const cal = $("#calendario");
  cal.innerHTML = "";
  const hojeNum = d.disponivel ? d.dia : ((d.sequencia - 1) % 7) + 1;
  d.calendario.forEach((premio, i) => {
    const n = i + 1;
    const dia = el("div", "dia");
    if (n < hojeNum || (!d.disponivel && n === hojeNum)) dia.classList.add("feito");
    if (d.disponivel && n === hojeNum) dia.classList.add("hoje");
    let img = `${ARTE}jogo/moeda.svg`, txt = `+${premio.moedas}`;
    if (premio.bau) { img = `${ARTE}baus/${premio.bau}.svg`; txt = CAT.baus[premio.bau].curto; }
    else if (premio.petiscos && !premio.moedas) { img = `${ARTE}jogo/petisco.svg`; txt = `x${premio.petiscos}`; }
    else if (premio.petiscos) txt = `+${premio.moedas} · x${premio.petiscos}`;
    dia.innerHTML = `Dia ${n}<img class="pixel" src="${img}" alt=""><b>${txt}</b>`;
    if (dia.classList.contains("feito")) dia.innerHTML += `<span class="feito-ic">${ic("check")}</span>`;
    cal.appendChild(dia);
  });
  $("#bt-diario").disabled = !d.disponivel;
  $("#bt-diario").textContent = d.disponivel ? "Pegar recompensa" : "Volte amanhã!";

  const rumo = $("#rumo-bau");
  rumo.innerHTML = "";
  for (let i = 0; i < CAT.atendimentos_por_bau; i++) {
    rumo.appendChild(el("i", i < EST.perfil.rumo_ao_bau ? "cheia" : ""));
  }
  $("#rumo-texto").textContent = EST.perfil.bau_pendente
    ? "Baú esperando um espaço livre!"
    : `atendimentos de ${Math.round(CAT.atendimento_minimo_s / 60)}+ min contam`;

  const espacos = $("#espacos");
  espacos.innerHTML = "";
  const alguemDestravando = EST.baus.some((b) => b && b.situacao === "destravando");
  EST.baus.forEach((b, i) => {
    if (!b) {
      espacos.appendChild(el("div", "espaco vazio", "Espaço livre<br><small>Atenda clientes para ganhar baús</small>"));
      return;
    }
    const e = el("div", `espaco ${b.situacao}`);
    e.innerHTML = `<div class="nome-bau">${b.nome}</div><img src="${ARTE}baus/${b.tipo}.svg" alt="">`;
    if (b.situacao === "pronto") {
      e.appendChild(el("div", "estado-bau", "ABRIR!"));
      e.addEventListener("click", () => abrirBau(i, false));
    } else if (b.situacao === "destravando") {
      e.appendChild(el("div", "estado-bau", `<span data-falta="${b.falta_s}">${tempo(b.falta_s)}</span>`));
      const bt = el("button", "bt bt-roxo", `Abrir já ${moedaImg}${b.custo_agora}`);
      bt.addEventListener("click", (ev) => { ev.stopPropagation(); abrirBau(i, true); });
      e.appendChild(bt);
    } else {
      e.appendChild(el("div", "estado-bau", duracao(b.minutos)));
      const bt = alguemDestravando
        ? el("button", "bt bt-roxo", `Abrir já ${moedaImg}${b.custo_agora}`)
        : el("button", "bt bt-azul", "Destravar");
      bt.addEventListener("click", async (ev) => {
        ev.stopPropagation();
        if (alguemDestravando) return abrirBau(i, true);
        tocar("clique");
        await acao("destravar_bau", { espaco: i });
      });
      e.appendChild(bt);
    }
    espacos.appendChild(e);
  });
}

async function abrirBau(espaco, pagar) {
  if (animando) return;
  const r = await acao("abrir_bau", { espaco, pagar });
  if (r) await animarAbertura(r);
}
$("#bt-gratis").addEventListener("click", async () => {
  if (animando) return;
  const r = await acao("abrir_bau_gratis");
  if (r) await animarAbertura(r);
});
$("#bt-diario").addEventListener("click", async () => {
  if (animando) return;
  const r = await acao("resgatar_diario");
  if (!r) return;
  tocar("moeda");
  const p = r.premio;
  const partes = [];
  if (p.moedas) partes.push(`+${p.moedas} moedas`);
  if (p.petiscos) partes.push(`+${p.petiscos} petiscos`);
  avisar(`Dia ${((r.sequencia - 1) % 7) + 1}: ${partes.join(" e ") || "baú!"}`);
  confete({ particleCount: 60, spread: 70, origin: { y: 0.4 } });
  if (r.bau) await animarAbertura(r.bau);
});

/* ---------------- abertura de baú (a parte divertida) ---------------- */

let toqueResolver = null;
$("#abertura").addEventListener("click", () => { if (toqueResolver) { const r = toqueResolver; toqueResolver = null; r(); } });
function esperarToque(mostrarDica = true) {
  $("#dica-toque").style.visibility = mostrarDica ? "visible" : "hidden";
  return new Promise((r) => { toqueResolver = r; testeAutoToque(); });
}
const ordemRaridade = (c) => CAT.ordem_raridade.indexOf(carta(c.id).raridade);

async function animarAbertura(rec) {
  animando = true;
  const ov = $("#abertura");
  const bau = $("#abertura-bau");
  const raios = $("#raios");
  const titulo = $("#abertura-titulo");
  const revelacao = $("#revelacao");
  const restantes = $("#restantes");
  const cartas = [...rec.cartas].sort((a, b) => ordemRaridade(a) - ordemRaridade(b));
  const melhor = cartas.length ? CAT.raridades[carta(cartas[cartas.length - 1].id).raridade] : null;

  ov.hidden = false;
  $("#resumo").hidden = true;
  revelacao.innerHTML = "";
  titulo.textContent = rec.nome;
  bau.src = `${ARTE}baus/${rec.bau}.svg`;
  gsap.set([bau, titulo], { clearProps: "all" });
  gsap.set(raios, { opacity: 0, rotation: 0 });
  gsap.set(restantes, { opacity: 0 });
  gsap.from(titulo, { y: -60, opacity: 0, duration: 0.4, ease: "back.out(2)" });
  gsap.fromTo(bau, { y: -500, scale: 0.6 }, { y: 0, scale: 1, duration: 0.7, ease: "bounce.out" });
  tocar("carta");
  await esperarToque();

  // Treme cada vez mais forte e brilha com a cor da melhor carta lá dentro.
  tocar("abrir");
  const brilho = melhor ? melhor.cor : "#ffffff";
  await gsap.timeline()
    .to(bau, { rotation: -5, duration: 0.05, yoyo: true, repeat: 5 })
    .to(bau, { rotation: 8, scale: 1.08, duration: 0.05, yoyo: true, repeat: 7 })
    .to(bau, { rotation: -12, scale: 1.15, filter: `drop-shadow(0 0 30px ${brilho})`, duration: 0.04, yoyo: true, repeat: 9 })
    .to(bau, { scale: 1.6, opacity: 0, duration: 0.25, ease: "power2.in" });
  gsap.to(raios, { opacity: 1, duration: 0.3 });
  gsap.to(raios, { rotation: 360, duration: 24, ease: "none", repeat: -1 });
  gsap.to(titulo, { opacity: 0, duration: 0.3 });
  gsap.to(restantes, { opacity: 1, duration: 0.3 });

  for (let i = 0; i < cartas.length; i++) {
    restantes.textContent = cartas.length - i;
    await revelarCarta(cartas[i]);
  }
  gsap.to(restantes, { opacity: 0, duration: 0.2 });
  await mostrarResumo(rec, cartas);

  gsap.killTweensOf(raios);
  ov.hidden = true;
  animando = false;
  // Pede o estado atualizado (o Python já guardou tudo ao sortear).
  chamar("estado").then(aplicarEstado).catch(() => {});
}

async function revelarCarta(c) {
  const info = carta(c.id);
  const rar = CAT.raridades[info.raridade];
  const revelacao = $("#revelacao");
  revelacao.innerHTML = "";
  const giro = el("div", "carta-giro");
  const brilho = el("div", "brilho-raridade");
  brilho.style.background = rar.cor;
  const verso = el("div", "verso", "?");
  const face = el("div", "face");
  face.appendChild(cartaEl(c.id, { nivel: c.nivel, copias: c.copias, barra: false }));
  giro.append(brilho, verso, face);
  const infoEl = el("div", "revelacao-info");
  const precisaNv = c.precisa;
  infoEl.innerHTML = `<div class="raridade" style="color:${rar.cor}">${rar.nome}</div>`
    + (c.nova ? `<span class="novo">NOVA!</span>` : `<b>+${c.ganhas}</b> ${c.ganhas > 1 ? "cópias" : "cópia"}`)
    + (precisaNv ? `<div class="barra"><div></div><span>${c.copias}/${precisaNv}</span></div>` : "");
  revelacao.append(giro, infoEl);

  gsap.set(infoEl, { opacity: 0 });
  gsap.set(brilho, { opacity: 0 });
  await gsap.fromTo(giro, { y: 260, scale: 0.2, rotationY: 0 }, { y: 0, scale: 1, duration: 0.35, ease: "back.out(1.6)" });
  const especial = info.raridade === "lendaria" || info.raridade === "mitica";
  tocar(especial ? "lendaria" : "carta");
  await gsap.to(giro, { rotationY: 180, duration: 0.45, ease: "power2.out" });
  gsap.to(brilho, { opacity: info.raridade === "comum" ? 0.25 : 0.85, duration: 0.3 });
  gsap.to(infoEl, { opacity: 1, duration: 0.25 });
  if (precisaNv) {
    const antes = Math.max(0, c.nova ? c.copias : c.copias - c.ganhas);
    gsap.fromTo($(".barra > div", infoEl), { width: `${(100 * antes) / precisaNv}%` },
      { width: `${Math.min(100, (100 * c.copias) / precisaNv)}%`, duration: 0.6, delay: 0.2 });
  }
  if (info.raridade === "mitica") {
    gsap.to("#raios", { background: "repeating-conic-gradient(from 0deg, rgba(255,77,109,.30) 0deg 6deg, rgba(77,210,255,.25) 6deg 12deg, rgba(249,248,113,.25) 12deg 18deg, transparent 18deg 26deg)", duration: 0.3 });
    const cores = ["#ff4d6d", "#ffb84d", "#f9f871", "#4dffb8", "#4dd2ff", "#b44dff"];
    confete({ particleCount: 220, spread: 140, origin: { y: 0.55 }, colors: cores });
    setTimeout(() => confete({ particleCount: 120, angle: 60, spread: 70, origin: { x: 0, y: 0.7 }, colors: cores }), 250);
    setTimeout(() => confete({ particleCount: 120, angle: 120, spread: 70, origin: { x: 1, y: 0.7 }, colors: cores }), 450);
    gsap.fromTo("main, .abertura", { x: -12 }, { x: 0, duration: 0.6, ease: "elastic.out(1, 0.25)" });
  } else if (info.raridade === "lendaria") {
    gsap.to("#raios", { background: "repeating-conic-gradient(from 0deg, rgba(245,184,27,.25) 0deg 8deg, transparent 8deg 22deg)", duration: 0.3 });
    confete({ particleCount: 180, spread: 110, origin: { y: 0.55 }, colors: ["#f5b81b", "#fff3b0", "#ffffff", "#ff8a00"] });
    gsap.fromTo("main, .abertura", { x: -8 }, { x: 0, duration: 0.4, ease: "elastic.out(1, 0.3)" });
  } else if (info.raridade === "epica") {
    confete({ particleCount: 70, spread: 70, origin: { y: 0.55 }, colors: ["#a855f7", "#e9d5ff", "#ffffff"] });
  }
  await esperarToque();
  await gsap.to(giro, { x: -500, rotation: -20, opacity: 0, duration: 0.25, ease: "power2.in" });
  gsap.to("#raios", { background: "repeating-conic-gradient(from 0deg, rgba(255,255,255,.10) 0deg 8deg, transparent 8deg 22deg)", duration: 0.1 });
}

async function mostrarResumo(rec, cartas) {
  $("#revelacao").innerHTML = "";
  const resumo = $("#resumo");
  resumo.innerHTML = "";
  resumo.hidden = false;
  const titulo = el("h2", "", "Você ganhou!");
  const grade = el("div", "resumo-cartas");
  cartas.forEach((c) => {
    const cartaNode = cartaEl(c.id, { nivel: c.nivel, copias: c.copias });
    cartaNode.appendChild(el("span", "qtd", c.nova ? "NOVA" : `x${c.ganhas}`));
    grade.appendChild(cartaNode);
  });
  const recursos = el("div", "resumo-recursos");
  recursos.innerHTML = `<div class="recurso"><img src="${ARTE}jogo/moeda.svg" alt=""><span id="r-moedas">0</span></div>`
    + (rec.petiscos ? `<div class="recurso"><img class="pixel" src="${ARTE}jogo/petisco.svg" alt=""><span id="r-petiscos">0</span></div>` : "");
  const coletar = el("button", "bt bt-verde", "Coletar");
  resumo.append(titulo, grade, recursos, coletar);
  gsap.from(grade.children, { scale: 0, duration: 0.3, stagger: 0.05, ease: "back.out(2)" });
  const contador = { m: 0, p: 0 };
  gsap.to(contador, {
    m: rec.moedas, p: rec.petiscos, duration: 0.8, ease: "power1.out",
    onUpdate: () => {
      $("#r-moedas").textContent = Math.round(contador.m);
      if ($("#r-petiscos")) $("#r-petiscos").textContent = Math.round(contador.p);
    },
  });
  tocar("moeda");
  await esperarToque(false);
  tocar("clique");
}

/* ---------------- cartas ---------------- */

function arteDe(c) {
  const a = el("div");
  if (c.tipo === "tema") {
    const t = CAT.temas[c.alvo];
    a.className = "arte-tema";
    a.style.background = `linear-gradient(to right, ${t.previa[1]} 32%, ${t.previa[0]} 32%)`;
    a.innerHTML = `<span class="ponto-destaque" style="background:${t.previa[2]}"></span>`
      + (c.arte ? `<img src="${ARTE}${c.arte}" alt="">` : "")
      + `<span class="nome-fonte" style="font-family:'${t.fonte || "Noto Sans"}';color:${t.texto}">${t.nome}</span>`;
  } else if (c.tipo === "pet") {
    a.className = "arte-pet";
    a.innerHTML = `<img src="${ARTE}${c.arte}" alt="">`;
  } else if (c.tipo === "acessorio") {
    a.className = "arte-acc";
    const { lado, acima } = CAT.pet;
    const e = CAT.encaixes.slime[c.alvo];
    const alto = lado + acima;
    a.style.aspectRatio = `${lado} / ${alto}`;
    a.innerHTML = `<img class="sombra-pet" style="top:${(acima / alto) * 100}%" src="${ARTE}pets/slime.svg" alt="">`
      + `<img style="left:${(e.x / lado) * 100}%;top:${(e.y / alto) * 100}%;width:${(e.w / lado) * 100}%"`
      + ` src="${ARTE}${c.arte}" alt="">`;
  } else if (c.tipo === "moldura") {
    a.innerHTML = `<div class="amostra-avatar mold-${c.alvo}">AB</div>`;
    a.style.cssText = "width:100%;height:100%;display:grid;place-items:center";
  } else if (c.tipo === "som") {
    a.className = "arte-som";
    a.innerHTML = ic("speaker-high");
  }
  return a;
}

function cartaEl(id, { nivel, copias, barra = true, revelada = false } = {}) {
  const c = carta(id);
  const m = minha(id);
  nivel = nivel ?? (m ? m.nivel : 0);
  copias = copias ?? (m ? m.copias : 0);
  // revelada: mostra a arte mesmo sem ter a carta (na loja, a pessoa precisa ver o que compra).
  const node = el("div", `carta r-${c.raridade}` + (nivel || revelada ? "" : " bloqueada"));
  const arte = el("div", "carta-arte");
  arte.appendChild(arteDe(c));
  node.appendChild(arte);
  node.appendChild(el("div", "carta-nome", escapar(c.nome) + (nivel || revelada ? "" : ic("lock-simple"))));
  if (nivel) node.appendChild(el("div", "carta-nivel", nivel >= CAT.nivel_max ? "MÁX" : `Nv ${nivel}`));
  if (nivel && emUso(c)) node.appendChild(el("div", "carta-uso", "EM USO"));
  const p = precisa(nivel);
  if (barra && nivel && p) {
    const b = el("div", "barra" + (copias >= p ? " pode" : ""),
      `<div style="width:${Math.min(100, (100 * copias) / p)}%"></div><span>${copias >= p ? ic("arrow-fat-up") + " " : ""}${copias}/${p}</span>`);
    node.appendChild(b);
  }
  return node;
}

function montarFiltros() {
  const f = $("#filtros");
  f.innerHTML = "";
  [["todas", "Todas"], ...Object.entries(CAT.tipos)].forEach(([chave, nome]) => {
    const b = el("button", "filtro" + (chave === filtro ? " ativo" : ""), nome);
    b.addEventListener("click", () => { filtro = chave; tocar("clique"); montarFiltros(); desenharColecao(); });
    f.appendChild(b);
  });
}

function desenharColecao() {
  const total = CAT.cartas.length;
  const tenho = CAT.cartas.filter((c) => minha(c.id)).length;
  $("#colecao-contagem").textContent = `${tenho}/${total}`;
  $("#colecao-barra").style.width = `${(100 * tenho) / total}%`;
  const grade = $("#grade-cartas");
  grade.innerHTML = "";
  CAT.cartas
    .filter((c) => filtro === "todas" || c.tipo === filtro)
    .forEach((c) => {
      const node = cartaEl(c.id);
      node.addEventListener("click", () => { tocar("clique"); abrirModal(c.id); });
      grade.appendChild(node);
    });
}

function abrirModal(id) {
  const c = carta(id);
  const m = minha(id);
  const rar = CAT.raridades[c.raridade];
  const caixa = $("#modal-caixa");
  caixa.innerHTML = "";
  caixa.appendChild(cartaEl(id));
  const d = el("div", "detalhe");
  d.innerHTML = `<h2>${c.nome}</h2>
    <span class="tag" style="background:${rar.cor}">${rar.nome}</span><span class="tag">${CAT.tipos[c.tipo]}</span>
    <p>${c.descricao}</p>`;
  const botoes = el("div", "botoes");
  const nota = el("div", "nota");
  if (!m) {
    nota.textContent = "Você ainda não tem essa carta. Encontre em baús ou na loja!";
  } else {
    const p = precisa(m.nivel);
    d.appendChild(el("div", "", `Nível <b>${m.nivel}</b> de ${CAT.nivel_max}`
      + (p ? ` · cópias <b>${m.copias}/${p}</b>` : " · nível máximo!")));
    if (c.tipo !== "som" || !emUso(c)) {
      const usar = el("button", "bt bt-verde", emUso(c) ? (c.tipo === "acessorio" ? "Tirar" : "Em uso") : "Usar");
      usar.disabled = emUso(c) && c.tipo !== "acessorio";
      usar.addEventListener("click", async () => {
        if (await acao("equipar", { id }) !== null) { tocar("pet_feliz"); fecharModal(); avisar(`${c.nome} equipado!`); }
      });
      botoes.appendChild(usar);
    } else {
      const desligar = el("button", "bt bt-azul", "Desligar som");
      desligar.addEventListener("click", async () => { await acao("equipar", { id }); fecharModal(); });
      botoes.appendChild(desligar);
    }
    if (p) {
      const custo = CAT.moedas_por_nivel[m.nivel - 1];
      const melhorar = el("button", "bt bt-ouro", `Melhorar ${moedaImg}${custo}`);
      melhorar.disabled = m.copias < p;
      melhorar.addEventListener("click", async () => {
        const r = await acao("melhorar_carta", { id });
        if (r) {
          tocar("melhorar");
          confete({ particleCount: 90, spread: 80, origin: { y: 0.5 } });
          avisar(`${c.nome} subiu para o nível ${r.nivel}!`);
          abrirModal(id);
        }
      });
      botoes.appendChild(melhorar);
      const falta = p - m.copias;
      if (falta > 0) nota.textContent = falta === 1 ? "Falta 1 cópia para o próximo nível." : `Faltam ${falta} cópias para o próximo nível.`;
    }
    if (c.tipo === "tema") {
      nota.innerHTML += m.nivel >= CAT.nivel_max
        ? ` ${ic("sparkle", "ic-brilho")} Nível máximo: versão dourada do tema ativada!`
        : " No nível 5 o tema ganha a versão dourada.";
    }
  }
  if (c.tipo === "som") {
    const ouvir = el("button", "bt bt-azul", `${ic("play")} Ouvir`);
    ouvir.addEventListener("click", () => {
      const a = new Audio(`${SONS}${c.alvo}.wav`); a.play().catch(() => {});
    });
    botoes.appendChild(ouvir);
  }
  d.append(botoes, nota);
  caixa.appendChild(d);
  $("#modal").hidden = false;
  gsap.from(caixa, { scale: 0.85, opacity: 0, duration: 0.2, ease: "back.out(2)" });
}
function fecharModal() { $("#modal").hidden = true; }
$("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") fecharModal(); });

/* ---------------- pet ---------------- */

let toquesOvo = 0;

function petEl(especie, acessorio, largura) {
  const { lado, acima } = CAT.pet;
  const u = largura / lado;
  const p = el("div", "pet");
  p.style.width = `${largura}px`;
  p.style.height = `${(lado + acima) * u}px`;
  p.innerHTML = `<img style="top:${acima * u}px" src="${ARTE}pets/${especie}.svg" alt="">`;
  if (acessorio) {
    const e = CAT.encaixes[especie][acessorio];
    p.innerHTML += `<img style="left:${e.x * u}px;top:${e.y * u}px;width:${e.w * u}px"`
      + ` src="${ARTE}acessorios/${acessorio}.svg" alt="">`;
  }
  return p;
}

function desenharPet() {
  const pet = EST.pet;
  const area = $("#pet-area");
  // Só refaz o desenho (e reinicia a animação) quando a aparência do pet mudou; senão o pet
  // daria um tranco a cada atualização do estado.
  const chave = [pet.chocado, pet.especie, pet.acessorio, pet.tamanho, pet.humor, pet.dormindo].join("|");
  const mudou = area.dataset.chave !== chave;
  if (mudou) {
    area.dataset.chave = chave;
    gsap.killTweensOf(area);
    gsap.set(area, { clearProps: "transform" });
    area.innerHTML = "";
    // Cada pixel do desenho vira 4 a 5 px na tela (múltiplos de 0,5 para a pixel art não deformar).
    const lado = CAT.pet.lado;
    if (!pet.chocado) {
      area.appendChild(petEl("ovo", null, lado * 4));
    } else {
      const px = Math.round(10 * pet.tamanho) / 2;  // bebê 4, jovem 4,5, adulto 5
      area.appendChild(petEl(pet.especie, pet.acessorio, lado * px));
    }
  }
  $("#palco").classList.toggle("noite", pet.dormindo);
  $("#pet-fala").textContent = pet.fala;
  $("#pet-nome").textContent = pet.nome;
  $("#pet-estagio").textContent = pet.chocado ? `${pet.estagio} · ${pet.xp} XP` : "Ovo";
  const ate = pet.xp_proximo;
  $("#pet-xp").style.width = ate ? `${(100 * pet.xp) / ate}%` : "100%";
  $("#pet-xp-texto").textContent = !pet.chocado ? "Choque o ovo!" : ate ? `${pet.xp}/${ate} XP para crescer` : "Totalmente crescido!";

  const atributos = $("#atributos");
  atributos.innerHTML = "";
  if (pet.chocado) {
    [["fome", "cookie", "comida", "Comida"], ["alegria", "heart", "alegria", "Alegria"],
     ["energia", "lightning", "energia", "Energia"]].forEach(([chave, icone, cor, nome]) => {
      const v = pet[chave];
      atributos.appendChild(el("div", `atributo ${chave}`,
        `<span>${ic(icone, "ic-" + cor)}${nome}</span><div class="barra"><div class="${v < 30 ? "baixo" : ""}" style="width:${v}%"></div><span>${v}%</span></div>`));
    });
  } else {
    atributos.appendChild(el("p", "ovo-dica", "Toque três vezes no ovo para descobrir quem está aí dentro!"));
  }

  const acoes = $("#acoes-pet");
  acoes.innerHTML = "";
  if (pet.chocado) {
    const comer = el("button", "bt bt-ouro", `${ic("cookie")} Alimentar (${EST.perfil.petiscos})`);
    comer.disabled = pet.dormindo;
    comer.addEventListener("click", () => acaoPet("alimentar", comer));
    const brincar = el("button", "bt bt-azul",
      `${ic("tennis-ball")} Brincar` + (pet.brincar_em_s > 0
        ? ` (<span data-falta="${pet.brincar_em_s}">${tempo(pet.brincar_em_s)}</span>)` : ""));
    brincar.disabled = pet.dormindo || pet.brincar_em_s > 0;
    brincar.addEventListener("click", () => acaoPet("brincar", brincar));
    const sono = el("button", "bt bt-roxo", pet.dormindo ? `${ic("sun")} Acordar` : `${ic("moon-stars")} Soneca`);
    sono.addEventListener("click", () => acaoPet(pet.dormindo ? "acordar" : "soneca", sono));
    acoes.append(comer, brincar, sono);
  }

  // Guarda-roupa separado por tipo; o que falta aparece apagado, para dar vontade de colecionar.
  $("#guarda-roupa").hidden = !pet.chocado;
  $("#bt-renomear").hidden = !pet.chocado;
  for (const tipo of ["pet", "acessorio"]) {
    const destino = $(tipo === "pet" ? "#roupas-especies" : "#roupas-acessorios");
    destino.innerHTML = "";
    const todas = CAT.cartas.filter((c) => c.tipo === tipo);
    $(tipo === "pet" ? "#conta-especies" : "#conta-acessorios").textContent =
      `${todas.filter((c) => minha(c.id)).length}/${todas.length}`;
    if (tipo === "acessorio") {
      const nenhum = el("button", "roupa" + (pet.acessorio ? "" : " ativa"), `<span class="nenhum">${ic("prohibit")}</span>`);
      nenhum.title = "Sem acessório";
      nenhum.addEventListener("click", async () => {
        const atual = CAT.cartas.find((c) => c.tipo === "acessorio" && c.alvo === pet.acessorio);
        if (atual && await acao("equipar", { id: atual.id }) !== null) tocar("clique");
      });
      destino.appendChild(nenhum);
    }
    todas.forEach((c) => {
      const tenho = Boolean(minha(c.id));
      const r = el("button", "roupa" + (emUso(c) ? " ativa" : "") + (tenho ? "" : " bloqueada"),
        `<img src="${ARTE}${c.arte}" alt="">`);
      r.title = tenho ? c.nome : `${c.nome} (${CAT.raridades[c.raridade].nome}) · encontre em baús`;
      r.addEventListener("click", async () => {
        if (!tenho) { avisar(`${c.nome}: encontre em baús ou na loja.`, "lock-simple"); return; }
        if (await acao("equipar", { id: c.id }) !== null) tocar("pet_feliz");
      });
      destino.appendChild(r);
    });
  }
  if (mudou && $("#tela-pet").classList.contains("ativa")) animarPetParado();
}

function animarPetParado() {
  const area = $("#pet-area");
  gsap.killTweensOf(area);
  if (!EST || EST.pet.dormindo) return;
  if (!EST.pet.chocado) {
    gsap.to(area, { rotation: 4, duration: 0.6, yoyo: true, repeat: -1, ease: "sine.inOut", transformOrigin: "50% 100%" });
  } else if (EST.pet.humor === "feliz") {
    gsap.to(area, { y: -14, duration: 0.45, yoyo: true, repeat: -1, ease: "power1.out" });
  } else if (EST.pet.humor === "triste") {
    gsap.to(area, { scaleY: 0.94, duration: 1.6, yoyo: true, repeat: -1, ease: "sine.inOut", transformOrigin: "50% 100%" });
  } else {
    gsap.to(area, { scaleY: 0.97, scaleX: 1.02, duration: 1, yoyo: true, repeat: -1, ease: "sine.inOut", transformOrigin: "50% 100%" });
  }
}

$("#pet-area").addEventListener("click", async () => {
  const area = $("#pet-area");
  if (!EST.pet.chocado) {
    toquesOvo += 1;
    tocar("clique");
    gsap.fromTo(area, { rotation: -14 }, { rotation: 14, duration: 0.07, yoyo: true, repeat: 3, transformOrigin: "50% 100%" });
    if (toquesOvo >= 3) {
      toquesOvo = 0;
      const pet = await acao("pet_chocar");
      if (pet) {
        tocar("lendaria");
        confete({ particleCount: 120, spread: 90, origin: { y: 0.6 } });
        avisar(`Nasceu um ${carta("pet-" + pet.especie).nome}! Dê um nome a ele.`);
        gsap.from("#pet-area", { scale: 0, duration: 0.6, ease: "back.out(3)" });
      }
    }
    return;
  }
  if (EST.pet.dormindo) { avisar("Shhh... está dormindo."); return; }
  tocar("pet_feliz");
  coracao();
  gsap.fromTo(area, { y: 0 }, { y: -40, duration: 0.18, yoyo: true, repeat: 1, ease: "power2.out", onComplete: animarPetParado });
});

// Partícula que sobe do pet (coração, biscoito, estrela...).
const COR_PARTICULA = { heart: "ic-alegria", cookie: "ic-comida", star: "ic-estrela" };
function coracao(icone = "heart") {
  const palco = $("#palco");
  const c = el("div", "", ic(icone, COR_PARTICULA[icone] || ""));
  c.style.cssText = "position:absolute;bottom:45%;left:50%;font-size:32px;z-index:4;pointer-events:none;"
    + "filter:drop-shadow(0 2px 0 rgba(0,0,0,.3))";
  palco.appendChild(c);
  gsap.to(c, { y: -120, x: (Math.random() - 0.5) * 120, opacity: 0, duration: 1.2, ease: "power1.out", onComplete: () => c.remove() });
}

async function acaoPet(nome, botao) {
  const pet = await acao("pet_acao", { acao: nome });
  if (!pet) return;
  const area = $("#pet-area");
  if (nome === "alimentar") {
    tocar("nhac");
    const b = botao.getBoundingClientRect();
    const a = area.getBoundingClientRect();
    const petisco = el("img", "pixel", "");
    petisco.src = `${ARTE}jogo/petisco.svg`;
    petisco.style.cssText = `position:fixed;width:40px;left:${b.left}px;top:${b.top}px;z-index:60`;
    document.body.appendChild(petisco);
    gsap.to(petisco, { left: a.left + a.width / 2 - 20, top: a.top + a.height / 2, duration: 0.5, ease: "power2.in",
      onComplete: () => { petisco.remove(); gsap.fromTo($("#pet-area"), { scaleY: 0.8, scaleX: 1.15 }, { scaleY: 1, scaleX: 1, duration: 0.4, ease: "elastic.out(1, 0.4)", transformOrigin: "50% 100%" }); coracao("cookie"); } });
  } else if (nome === "brincar") {
    tocar("pet_feliz");
    gsap.fromTo($("#pet-area"), { rotation: 0 }, { rotation: 360, y: -60, duration: 0.6, ease: "power2.out", yoyo: true, repeat: 1, onComplete: animarPetParado });
    coracao(); coracao("star");
  } else if (nome === "soneca") {
    avisar(`${EST.pet.nome} foi tirar uma soneca.`);
  }
}

$("#bt-renomear").addEventListener("click", () => $("#pet-nome").click());
$("#pet-nome").addEventListener("click", () => {
  if (!EST.pet.chocado) return;
  const bt = $("#pet-nome");
  const input = el("input");
  input.value = EST.pet.nome;
  input.maxLength = 20;
  input.style.cssText = "font:30px Bangers;width:220px;border-radius:10px;border:3px solid #0a0f22;padding:2px 8px";
  bt.replaceWith(input);
  input.focus();
  input.select();
  const salvar = async () => {
    input.replaceWith(bt);
    if (input.value.trim() && input.value.trim() !== EST.pet.nome) {
      if (await acao("pet_renomear", { nome: input.value }) !== null) avisar("Nome novo, quem é o pet mais lindo?");
    }
  };
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") input.blur(); if (e.key === "Escape") { input.value = ""; input.blur(); } });
  input.addEventListener("blur", salvar, { once: true });
});

/* ---------------- loja ---------------- */

function desenharLoja() {
  const agora = new Date();
  const meiaNoite = new Date(agora); meiaNoite.setHours(24, 0, 0, 0);
  $("#loja-renova").innerHTML = `· novas ofertas em <span data-falta="${(meiaNoite - agora) / 1000 + passou()}">${tempo((meiaNoite - agora) / 1000)}</span>`;
  const ofertas = $("#ofertas");
  ofertas.innerHTML = "";
  EST.loja.ofertas.forEach((o) => {
    const box = el("div", "painel oferta" + (o.comprada ? " comprada" : ""));
    box.appendChild(cartaEl(o.carta, { barra: false, revelada: true }));
    const bt = el("button", "bt bt-ouro", o.comprada ? `${ic("check")} Comprado` : `${moedaImg}${o.preco}`);
    bt.disabled = o.comprada;
    bt.addEventListener("click", async () => {
      const r = await acao("comprar_oferta", { indice: o.indice });
      if (r) {
        tocar(["lendaria", "mitica"].includes(carta(r.id).raridade) ? "lendaria" : "moeda");
        confete({ particleCount: 80, spread: 70, origin: { y: 0.5 } });
        avisar(r.nova ? `Carta nova: ${carta(r.id).nome}!` : `+1 cópia de ${carta(r.id).nome}`);
      }
    });
    box.appendChild(bt);
    ofertas.appendChild(box);
  });
  $$("[data-petiscos]").forEach((bt) => {
    const n = Number(bt.dataset.petiscos);
    bt.innerHTML = `${moedaImg}${n * EST.loja.preco_petisco}`;
    bt.onclick = async () => {
      if (await acao("comprar_petiscos", { quantidade: n }) !== null) { tocar("nhac"); avisar(`+${n} petisco${n > 1 ? "s" : ""}!`); }
    };
  });
}

/* ---------------- modo de teste (fora do app) ---------------- */
// Fora do WebKit do app não há ponte com o Python: usa dados de exemplo (window.TESTE) para
// conferir o visual num navegador comum. Ex.: jogo.html#pet ou #abrir:3 (abre e avança 3 toques).

function testeResponder(acaoNome) {
  if (!window.TESTE) return Promise.reject(new Error("Sem conexão com o app."));
  if (acaoNome === "abrir_bau" || acaoNome === "abrir_bau_gratis") return Promise.resolve(window.TESTE.recompensa);
  return Promise.resolve(EST);
}
let testeToques = 0;
function testeAutoToque() {
  if (!window.TESTE || testeToques <= 0) return;
  testeToques -= 1;
  setTimeout(() => { if (toqueResolver) { const r = toqueResolver; toqueResolver = null; r(); } }, 300);
}
if (window.TESTE) {
  window.__iniciar(window.TESTE.catalogo, window.TESTE.estado);
  const [tela, n] = location.hash.slice(1).split(":");
  if (tela === "abrir") {
    gsap.globalTimeline.timeScale(8);  // acelera para o teste não demorar
    testeToques = Number(n || 0);
    animarAbertura(window.TESTE.recompensa);
  }
  else if (tela === "modal") abrirModal(n);

  else if (tela) irPara(tela);
}
