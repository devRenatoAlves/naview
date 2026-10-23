"""Motor do jogo: guarda o progresso (SQLite local) e aplica todas as regras.

A interface só chama os métodos públicos daqui e mostra o resultado. Para levar o jogo a um
servidor da equipe, basta trocar esta classe por outra com os mesmos métodos que fale com a API
(os sorteios passariam a ser feitos lá, onde ninguém consegue editar).
"""
import datetime
import json
import math
import os
import random
import sqlite3
import time
from collections import Counter
from pathlib import Path

import plataforma

from . import catalogo as cat

ARQUIVO = plataforma.DADOS / "progresso.db"
HORA = 3600
APP_FECHADO_S = 600  # sem "batimento" do app por mais que isso = app fechado (pet dormindo)


def _nome_do_pet(pet):
    """O nome do pet é sempre o da espécie (o nome da carta); não dá para mudar."""
    carta = cat.CARTAS_POR_ID.get(f"pet-{pet['especie']}") if pet["especie"] else None
    return carta["nome"] if carta else "Ovo"


class ErroJogo(Exception):
    """Ação não permitida (sem moedas, baú trancado...). A mensagem vai direto para a tela."""


class Progresso:
    def __init__(self, caminho=None, agora=time.time, hoje=datetime.date.today, rnd=None,
                 tema_atual=None, liberar_tudo=False):
        self.agora = agora
        self.hoje = hoje
        self.rnd = rnd or random.Random()
        demo = bool(os.environ.get("NAVIEW_DEMO_DOURADO")) and caminho is None
        if demo:  # só desenvolvimento: banco descartável, o progresso real não é tocado
            caminho = plataforma.CACHE / "progresso_demo.db"
            Path(caminho).unlink(missing_ok=True)
        caminho = caminho or ARQUIVO
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(caminho))
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS kv (chave TEXT PRIMARY KEY, valor TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS cartas (id TEXT PRIMARY KEY, nivel INTEGER NOT NULL,
                                               copias INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS baus (espaco INTEGER PRIMARY KEY, tipo TEXT NOT NULL,
                                             destrava_em REAL);
            CREATE TABLE IF NOT EXISTS atendimentos (id INTEGER PRIMARY KEY, contato TEXT,
                                                     fim REAL, segundos INTEGER);
        """)
        if self._kv("perfil") is None:
            self._comecar(tema_atual)
        self._migrar_pets()
        if demo:
            self._montar_demo_dourado()
        if liberar_tudo:  # modo de teste: todas as cartas, inclusive as que entrarem depois
            with self.db:
                self.db.executemany("INSERT OR IGNORE INTO cartas VALUES (?, 1, 0)",
                                    [(c["id"],) for c in cat.CARTAS])

    def _montar_demo_dourado(self):
        """Só para ver o design (NAVIEW_DEMO_DOURADO=1): um tema de cada raridade no nível máximo,
        a moldura dourada equipada e moedas de sobra. Roda num banco temporário."""
        temas = ["tema-padrao", "tema-oceano", "tema-terminal", "tema-espaco", "tema-pixel"]
        with self.db:
            self.db.executemany("INSERT OR REPLACE INTO cartas VALUES (?, ?, 0)",
                                [(t, cat.NIVEL_MAX) for t in temas])
            self.db.execute("INSERT OR REPLACE INTO cartas VALUES ('mold-dourada', 1, 0)")
            equipados = self._kv("equipados")
            equipados["moldura"] = "dourada"
            self._salvar_kv("equipados", equipados)

    def _migrar_pets(self):
        """Tira do progresso as cartas que saíram do catálogo (pets antigos, óculos). Se o pet atual era um
        deles, ele vira o Slime, mantendo nome, XP e acessório; um acessório removido sai do pet."""
        with self.db:
            for (cid,) in self.db.execute("SELECT id FROM cartas").fetchall():
                if cid not in cat.CARTAS_POR_ID:
                    self.db.execute("DELETE FROM cartas WHERE id = ?", (cid,))
            pet = self._kv("pet")
            if pet and pet.get("acessorio") and pet["acessorio"] not in cat.ENCAIXE_ACESSORIO:
                pet["acessorio"] = None  # acessório que saiu do catálogo (ex.: óculos)
                self._salvar_kv("pet", pet)
            if pet and pet["especie"] and f"pet-{pet['especie']}" not in cat.CARTAS_POR_ID:
                pet["especie"] = "slime"
                self._salvar_kv("pet", pet)
                self.db.execute("INSERT OR IGNORE INTO cartas VALUES ('pet-slime', 1, 0)")

    # ---- armazenamento --------------------------------------------------------

    def _kv(self, chave, padrao=None):
        linha = self.db.execute("SELECT valor FROM kv WHERE chave = ?", (chave,)).fetchone()
        return json.loads(linha[0]) if linha else padrao

    def _salvar_kv(self, chave, valor):
        self.db.execute("INSERT OR REPLACE INTO kv VALUES (?, ?)", (chave, json.dumps(valor)))

    def _comecar(self, tema_atual):
        agora = self.agora()
        with self.db:
            self._salvar_kv("perfil", {"moedas": 50, "petiscos": 3, "xp": 0,
                                       "atendimentos": 0, "rumo_ao_bau": 0, "bau_pendente": False,
                                       "baus_sem_lendaria": 0})
            self._salvar_kv("gratis", {"qtd": 1, "desde": agora})
            self._salvar_kv("diario", {"ultimo": None, "sequencia": 0})
            self._salvar_kv("equipados", {"moldura": "simples", "som": None})
            self._salvar_kv("pet", {"especie": None, "acessorio": None,
                                    "fome": 80, "alegria": 80, "energia": 80, "xp": 0,
                                    "atualizado": agora, "visto": agora, "dormindo_ate": None,
                                    "ultimo_brincar": 0})
            iniciais = list(cat.INICIAIS)
            alvo = f"tema-{tema_atual}" if tema_atual else None
            if alvo in cat.CARTAS_POR_ID and alvo not in iniciais:
                iniciais.append(alvo)  # quem já usava um tema não perde ele
            for cid in iniciais:
                self.db.execute("INSERT OR IGNORE INTO cartas VALUES (?, 1, 0)", (cid,))
            # Presente de boas-vindas: um baú de prata já no primeiro espaço.
            self.db.execute("INSERT INTO baus VALUES (0, 'prata', NULL)")

    # ---- consultas ------------------------------------------------------------

    def cartas(self):
        return {cid: {"nivel": nivel, "copias": copias}
                for cid, nivel, copias in self.db.execute("SELECT id, nivel, copias FROM cartas")}

    def possui(self, cid):
        return self.db.execute("SELECT 1 FROM cartas WHERE id = ?", (cid,)).fetchone() is not None

    def possui_tema(self, chave):
        return self.possui(f"tema-{chave}")

    def nivel_carta(self, cid):
        linha = self.db.execute("SELECT nivel FROM cartas WHERE id = ?", (cid,)).fetchone()
        return linha[0] if linha else 0

    def equipados(self):
        return self._kv("equipados")

    def perfil(self):
        perfil = self._kv("perfil")
        nivel, resto = 1, perfil["xp"]
        while resto >= cat.xp_para_nivel(nivel):
            resto -= cat.xp_para_nivel(nivel)
            nivel += 1
        return dict(perfil, nivel=nivel, xp_no_nivel=resto, xp_proximo=cat.xp_para_nivel(nivel))

    def estado(self):
        """Tudo que a tela do jogo precisa para se desenhar."""
        agora = self.agora()
        self._atualizar_gratis()
        pet = self._pet_atualizado()
        baus = []
        for espaco in range(cat.ESPACOS_BAU):
            linha = self.db.execute("SELECT tipo, destrava_em FROM baus WHERE espaco = ?",
                                    (espaco,)).fetchone()
            if not linha:
                baus.append(None)
                continue
            tipo, destrava_em = linha
            situacao = ("trancado" if destrava_em is None else
                        "pronto" if destrava_em <= agora else "destravando")
            baus.append({"espaco": espaco, "tipo": tipo, "nome": cat.BAUS[tipo]["nome"],
                         "situacao": situacao, "minutos": cat.BAUS[tipo]["minutos"],
                         "falta_s": max(0, int((destrava_em or 0) - agora)) if destrava_em else None,
                         "custo_agora": self._custo_abrir_agora(tipo, destrava_em)})
        gratis = self._kv("gratis")
        diario = self._kv("diario")
        return {
            "perfil": self.perfil(),
            "cartas": self.cartas(),
            "baus": baus,
            "gratis": {"qtd": gratis["qtd"], "max": cat.BAU_GRATIS_MAX,
                       "proximo_s": (None if gratis["qtd"] >= cat.BAU_GRATIS_MAX else
                                     int(gratis["desde"] + cat.BAU_GRATIS_HORAS * HORA - agora))},
            "diario": {"disponivel": diario["ultimo"] != self.hoje().isoformat(),
                       "sequencia": diario["sequencia"], "dia": self._dia_sequencia(),
                       "calendario": cat.SEQUENCIA},
            "pet": self._pet_publico(pet),
            "loja": self._loja(),
            "equipados": self.equipados(),
        }

    def novidades(self, estado=None):
        """Quantas coisas esperam o usuário (para a bolinha no botão do jogo).

        estado: o de estado(), se já foi calculado (evita calcular tudo duas vezes)."""
        estado = estado or self.estado()
        prontos = sum(1 for b in estado["baus"] if b and b["situacao"] == "pronto")
        pet = estado["pet"]
        return (prontos + estado["gratis"]["qtd"] + int(estado["diario"]["disponivel"])
                + int(pet["chocado"] and pet["humor"] == "triste"))

    # ---- atendimentos -----------------------------------------------------------

    def registrar_atendimento(self, contato, segundos):
        """Chamado quando uma sessão termina. Só conta se durou o mínimo e se o mesmo ID ainda não
        atingiu o limite das últimas 24 h (devolve {"limitado": True} nesse caso)."""
        if segundos < cat.ATENDIMENTO_MINIMO_S:
            return None
        # Anti-trapaça: o mesmo ID conta no máximo ATENDIMENTOS_MAX_POR_ID vezes por janela de 24 h.
        # Sem ID conhecido (sessão capturada sem ID no título) não dá para conferir, então conta.
        contato = "".join(str(contato).split()) if contato else None
        if contato:
            desde = self.agora() - cat.ATENDIMENTOS_JANELA_H * HORA
            recentes = self.db.execute(
                "SELECT COUNT(*) FROM atendimentos WHERE REPLACE(contato, ' ', '') = ? AND fim > ?",
                (contato, desde)).fetchone()[0]
            if recentes >= cat.ATENDIMENTOS_MAX_POR_ID:
                return {"limitado": True, "moedas": 0, "xp": 0, "bau": None}
        resultado = {"moedas": cat.MOEDAS_ATENDIMENTO, "xp": cat.XP_ATENDIMENTO, "bau": None}
        with self.db:
            self.db.execute("INSERT INTO atendimentos (contato, fim, segundos) VALUES (?, ?, ?)",
                            (contato, self.agora(), int(segundos)))
            perfil = self._kv("perfil")
            perfil["atendimentos"] += 1
            perfil["moedas"] += cat.MOEDAS_ATENDIMENTO
            perfil["xp"] += cat.XP_ATENDIMENTO
            perfil["rumo_ao_bau"] += 1
            if perfil["rumo_ao_bau"] >= cat.ATENDIMENTOS_POR_BAU:
                perfil["rumo_ao_bau"] = 0
                perfil["bau_pendente"] = True
            self._salvar_kv("perfil", perfil)
            resultado["bau"] = self._entregar_bau_pendente()
            pet = self._pet_atualizado()
            if pet["especie"]:
                pet["xp"] += 3
                self._salvar_kv("pet", pet)
        resultado["rumo_ao_bau"] = self._kv("perfil")["rumo_ao_bau"]
        return resultado

    def _entregar_bau_pendente(self):
        perfil = self._kv("perfil")
        if not perfil["bau_pendente"]:
            return None
        livre = self._espaco_livre()
        if livre is None:
            return None  # fica guardado até liberar um espaço
        tipos, pesos = zip(*cat.SORTEIO_BAU_TRABALHO.items())
        tipo = self.rnd.choices(tipos, pesos)[0]
        self.db.execute("INSERT INTO baus VALUES (?, ?, NULL)", (livre, tipo))
        perfil["bau_pendente"] = False
        self._salvar_kv("perfil", perfil)
        return tipo

    def _espaco_livre(self):
        ocupados = {e for (e,) in self.db.execute("SELECT espaco FROM baus")}
        return next((e for e in range(cat.ESPACOS_BAU) if e not in ocupados), None)

    # ---- baús ------------------------------------------------------------------

    def destravar_bau(self, espaco):
        linha = self.db.execute("SELECT tipo, destrava_em FROM baus WHERE espaco = ?",
                                (espaco,)).fetchone()
        if not linha:
            raise ErroJogo("Não há baú nesse espaço.")
        if linha[1] is not None:
            raise ErroJogo("Esse baú já está destravando.")
        if self.db.execute("SELECT 1 FROM baus WHERE destrava_em > ?", (self.agora(),)).fetchone():
            raise ErroJogo("Só um baú destrava por vez.")
        with self.db:
            self.db.execute("UPDATE baus SET destrava_em = ? WHERE espaco = ?",
                            (self.agora() + cat.BAUS[linha[0]]["minutos"] * 60, espaco))

    def _custo_abrir_agora(self, tipo, destrava_em):
        agora = self.agora()
        if destrava_em is not None and destrava_em <= agora:
            return 0
        restante_min = (destrava_em - agora) / 60 if destrava_em else cat.BAUS[tipo]["minutos"]
        return max(5, math.ceil(restante_min / 3))

    def abrir_bau(self, espaco, pagar=False):
        linha = self.db.execute("SELECT tipo, destrava_em FROM baus WHERE espaco = ?",
                                (espaco,)).fetchone()
        if not linha:
            raise ErroJogo("Não há baú nesse espaço.")
        tipo, destrava_em = linha
        custo = self._custo_abrir_agora(tipo, destrava_em)
        if custo and not pagar:
            raise ErroJogo("Esse baú ainda não destravou.")
        with self.db:
            if custo:
                self._gastar_moedas(custo)
            self.db.execute("DELETE FROM baus WHERE espaco = ?", (espaco,))
            recompensa = self._abrir(tipo)
            recompensa["novo_bau"] = self._entregar_bau_pendente()
        return recompensa

    def _atualizar_gratis(self):
        gratis = self._kv("gratis")
        if gratis["qtd"] >= cat.BAU_GRATIS_MAX:
            return
        periodo = cat.BAU_GRATIS_HORAS * HORA
        ganhos = int((self.agora() - gratis["desde"]) // periodo)
        if ganhos:
            gratis["qtd"] = min(cat.BAU_GRATIS_MAX, gratis["qtd"] + ganhos)
            gratis["desde"] = (self.agora() if gratis["qtd"] >= cat.BAU_GRATIS_MAX
                               else gratis["desde"] + ganhos * periodo)
            with self.db:
                self._salvar_kv("gratis", gratis)

    def abrir_bau_gratis(self):
        self._atualizar_gratis()
        gratis = self._kv("gratis")
        if gratis["qtd"] <= 0:
            raise ErroJogo("O baú grátis ainda está recarregando.")
        with self.db:
            if gratis["qtd"] >= cat.BAU_GRATIS_MAX:
                gratis["desde"] = self.agora()  # cheio: a recarga começa agora
            gratis["qtd"] -= 1
            self._salvar_kv("gratis", gratis)
            return self._abrir("madeira")

    def _abrir(self, tipo):
        """Sorteia o conteúdo de um baú e já guarda tudo (chamar dentro de uma transação)."""
        regras = cat.BAUS[tipo]
        perfil = self._kv("perfil")
        moedas = self.rnd.randint(*regras["moedas"])
        petiscos = self.rnd.randint(*regras["petiscos"])

        raridades = [self._sortear_raridade() for _ in range(regras["cartas"])]
        if regras["minimo"]:
            minimo = cat.ORDEM_RARIDADE.index(regras["minimo"])
            if max(cat.ORDEM_RARIDADE.index(r) for r in raridades) < minimo:
                raridades[-1] = regras["minimo"]
        topo = cat.ORDEM_RARIDADE.index("lendaria")
        if any(cat.ORDEM_RARIDADE.index(r) >= topo for r in raridades):
            perfil["baus_sem_lendaria"] = 0
        else:
            perfil["baus_sem_lendaria"] += 1
            if perfil["baus_sem_lendaria"] >= cat.GARANTIA_LENDARIA:
                raridades[-1] = "lendaria"
                perfil["baus_sem_lendaria"] = 0

        ganhas = Counter(self._sortear_carta(r) for r in raridades)
        cartas = []
        existentes = self.cartas()
        for cid, qtd in sorted(ganhas.items(),
                               key=lambda i: cat.ORDEM_RARIDADE.index(cat.CARTAS_POR_ID[i[0]]["raridade"])):
            if cid in existentes:
                nova = False
                self.db.execute("UPDATE cartas SET copias = copias + ? WHERE id = ?", (qtd, cid))
            else:
                nova = True  # a primeira cópia vira a carta; as outras contam para o nível 2
                self.db.execute("INSERT INTO cartas VALUES (?, 1, ?)", (cid, qtd - 1))
            cartas.append(dict(self._carta_publica(cid), ganhas=qtd, nova=nova))

        perfil["moedas"] += moedas
        perfil["petiscos"] += petiscos
        perfil["xp"] += 5 * regras["cartas"]
        self._salvar_kv("perfil", perfil)
        return {"bau": tipo, "nome": regras["nome"], "moedas": moedas, "petiscos": petiscos,
                "cartas": cartas}

    def _sortear_raridade(self):
        nomes = cat.ORDEM_RARIDADE
        return self.rnd.choices(nomes, [cat.RARIDADES[r]["peso"] for r in nomes])[0]

    def _sortear_carta(self, raridade):
        opcoes = [c["id"] for c in cat.CARTAS if c["raridade"] == raridade]
        return self.rnd.choice(opcoes)

    def _carta_publica(self, cid):
        linha = self.db.execute("SELECT nivel, copias FROM cartas WHERE id = ?", (cid,)).fetchone()
        nivel, copias = linha if linha else (0, 0)
        precisa = cat.COPIAS_POR_NIVEL[nivel - 1] if 0 < nivel < cat.NIVEL_MAX else None
        return {"id": cid, "nivel": nivel, "copias": copias, "precisa": precisa}

    # ---- cartas ------------------------------------------------------------------

    def melhorar_carta(self, cid):
        carta = self._carta_publica(cid)
        if not carta["nivel"]:
            raise ErroJogo("Você ainda não tem essa carta.")
        if carta["nivel"] >= cat.NIVEL_MAX:
            raise ErroJogo("Essa carta já está no nível máximo.")
        if carta["copias"] < carta["precisa"]:
            raise ErroJogo(f"Faltam {carta['precisa'] - carta['copias']} cópias.")
        custo = cat.MOEDAS_POR_NIVEL[carta["nivel"] - 1]
        with self.db:
            self._gastar_moedas(custo)
            self.db.execute("UPDATE cartas SET nivel = nivel + 1, copias = copias - ? WHERE id = ?",
                            (carta["precisa"], cid))
            perfil = self._kv("perfil")
            perfil["xp"] += cat.XP_POR_NIVEL[carta["nivel"] - 1]
            self._salvar_kv("perfil", perfil)
        return self._carta_publica(cid)

    def equipar(self, cid):
        """Equipa moldura, som, pet ou acessório. Temas são aplicados pelo app (temas.py)."""
        carta = cat.CARTAS_POR_ID.get(cid)
        if not carta or not self.possui(cid):
            raise ErroJogo("Você ainda não tem essa carta.")
        with self.db:
            if carta["tipo"] in ("moldura", "som"):
                equipados = self._kv("equipados")
                atual = equipados.get(carta["tipo"])
                # Clicar de novo no som equipado desliga o som.
                equipados[carta["tipo"]] = None if (carta["tipo"] == "som" and atual == carta["alvo"]) \
                    else carta["alvo"]
                self._salvar_kv("equipados", equipados)
            elif carta["tipo"] in ("pet", "acessorio"):
                pet = self._pet_atualizado()
                if not pet["especie"]:
                    raise ErroJogo("Choque o ovo primeiro!")
                if carta["tipo"] == "pet":
                    pet["especie"] = carta["alvo"]
                else:
                    pet["acessorio"] = None if pet["acessorio"] == carta["alvo"] else carta["alvo"]
                self._salvar_kv("pet", pet)

    def _gastar_moedas(self, valor):
        perfil = self._kv("perfil")
        if perfil["moedas"] < valor:
            raise ErroJogo(f"Faltam {valor - perfil['moedas']} moedas.")
        perfil["moedas"] -= valor
        self._salvar_kv("perfil", perfil)

    # ---- recompensa diária -------------------------------------------------------

    def _dia_sequencia(self):
        """Qual dia do calendário (1-7) o próximo resgate vai dar."""
        diario = self._kv("diario")
        return (self._nova_sequencia(diario) - 1) % len(cat.SEQUENCIA) + 1

    def _nova_sequencia(self, diario):
        hoje = self.hoje()
        if diario["ultimo"] is None:
            return 1
        ultimo = datetime.date.fromisoformat(diario["ultimo"])
        if ultimo == hoje:
            return diario["sequencia"]
        # Sábado e domingo não quebram a sequência; faltar num dia útil, sim.
        dia = ultimo + datetime.timedelta(days=1)
        while dia < hoje:
            if dia.weekday() < 5:
                return 1
            dia += datetime.timedelta(days=1)
        return diario["sequencia"] + 1

    def resgatar_diario(self):
        diario = self._kv("diario")
        hoje = self.hoje().isoformat()
        if diario["ultimo"] == hoje:
            raise ErroJogo("Você já pegou a recompensa de hoje. Volte amanhã!")
        sequencia = self._nova_sequencia(diario)
        premio = cat.SEQUENCIA[(sequencia - 1) % len(cat.SEQUENCIA)]
        with self.db:
            perfil = self._kv("perfil")
            perfil["moedas"] += premio.get("moedas", 0)
            perfil["petiscos"] += premio.get("petiscos", 0)
            self._salvar_kv("perfil", perfil)
            self._salvar_kv("diario", {"ultimo": hoje, "sequencia": sequencia})
            bau = self._abrir(premio["bau"]) if premio.get("bau") else None
        return {"sequencia": sequencia, "premio": premio, "bau": bau}

    # ---- loja ----------------------------------------------------------------------

    def _loja(self):
        """Ofertas do dia. Sorteadas uma vez por dia para cada usuário e guardadas: consultar a loja
        de novo (ou comprar) não muda o que está à venda."""
        hoje = self.hoje().isoformat()
        compradas = self._kv("loja", {}).get(hoje, [])
        dia = self._kv("loja_dia")
        if not dia or dia.get("dia") != hoje:
            especial = self.rnd.choice(["epica", "epica", "epica", "lendaria", "lendaria", "mitica"])
            raridades = ["comum", "rara", especial]
            self.rnd.shuffle(raridades)  # a ordem dos itens também é aleatória
            dia = {"dia": hoje, "ofertas": [
                {"carta": self.rnd.choice([c["id"] for c in cat.CARTAS if c["raridade"] == r]),
                 "preco": cat.PRECO_CARTA[r]} for r in raridades]}
            with self.db:
                self._salvar_kv("loja_dia", dia)
        ofertas = [dict(o, indice=i, comprada=i in compradas) for i, o in enumerate(dia["ofertas"])]
        return {"ofertas": ofertas, "preco_petisco": cat.PRECO_PETISCO}

    def comprar_oferta(self, indice):
        oferta = self._loja()["ofertas"][indice]
        if oferta["comprada"]:
            raise ErroJogo("Você já comprou essa oferta hoje.")
        with self.db:
            self._gastar_moedas(oferta["preco"])
            cid = oferta["carta"]
            nova = not self.possui(cid)
            if nova:
                self.db.execute("INSERT INTO cartas VALUES (?, 1, 0)", (cid,))
            else:
                self.db.execute("UPDATE cartas SET copias = copias + 1 WHERE id = ?", (cid,))
            hoje = self.hoje().isoformat()
            self._salvar_kv("loja", {hoje: self._kv("loja", {}).get(hoje, []) + [indice]})
        return dict(self._carta_publica(cid), ganhas=1, nova=nova)

    def comprar_petiscos(self, quantidade=1):
        with self.db:
            self._gastar_moedas(cat.PRECO_PETISCO * quantidade)
            perfil = self._kv("perfil")
            perfil["petiscos"] += quantidade
            self._salvar_kv("perfil", perfil)

    # ---- pet ------------------------------------------------------------------------

    def _pet_atualizado(self):
        """Aplica a passagem do tempo (fome, alegria, energia) desde a última vez."""
        pet = self._kv("pet")
        agora = self.agora()
        if not pet["especie"]:
            pet["atualizado"] = agora
            return pet
        # App fechado conta como o pet dormindo.
        dormindo_ate = pet["dormindo_ate"] or 0
        if agora - pet["visto"] > APP_FECHADO_S:
            dormindo_ate = max(dormindo_ate, agora)
        inicio = pet["atualizado"]
        fim_sono = min(max(dormindo_ate, inicio), agora)
        horas_sono = (fim_sono - inicio) / HORA
        horas_acordado = (agora - fim_sono) / HORA
        for atributo, queda in cat.PET_QUEDA_POR_HORA.items():
            if atributo == "energia":
                variacao = horas_sono * cat.PET_SONO_POR_HORA - horas_acordado * queda
            else:
                variacao = -(horas_sono * queda / 2 + horas_acordado * queda)
            pet[atributo] = max(0.0, min(100.0, pet[atributo] + variacao))
        pet["atualizado"] = agora
        if pet["dormindo_ate"] and pet["dormindo_ate"] <= agora:
            pet["dormindo_ate"] = None
        return pet

    def _pet_publico(self, pet):
        agora = self.agora()
        estagio = max((e for e in cat.PET_ESTAGIOS if pet["xp"] >= e[0]), key=lambda e: e[0])
        proximo = next((e[0] for e in cat.PET_ESTAGIOS if e[0] > pet["xp"]), None)
        dormindo = bool(pet["dormindo_ate"] and pet["dormindo_ate"] > agora)
        menor = min(pet["fome"], pet["alegria"], pet["energia"])
        humor = "dormindo" if dormindo else "feliz" if menor >= 60 else "normal" if menor >= 30 else "triste"
        if not pet["especie"]:
            fala = "Toque no ovo para chocar!"
        elif dormindo:
            fala = "Zzz..."
        elif pet["fome"] < 30:
            fala = "Tô com fome!"
        elif pet["energia"] < 30:
            fala = "Que sono... uma soneca cairia bem."
        elif pet["alegria"] < 30:
            fala = "Brinca comigo?"
        elif humor == "feliz":
            # Muda a cada 10 min (e não a cada atualização da tela).
            fala = random.Random(int(agora // 600)).choice(["Bora atender!", "Você é o melhor!", "Mais um cliente feliz!",
                                    "Adoro trabalhar com você!"])
        else:
            fala = "Tudo tranquilo por aqui."
        espera = int(pet["ultimo_brincar"] + cat.PET_BRINCAR_ESPERA_MIN * 60 - agora)
        return {
            "nome": _nome_do_pet(pet), "especie": pet["especie"], "acessorio": pet["acessorio"],
            "chocado": bool(pet["especie"]),
            "fome": round(pet["fome"]), "alegria": round(pet["alegria"]), "energia": round(pet["energia"]),
            "xp": pet["xp"], "estagio": estagio[1], "tamanho": estagio[2], "xp_proximo": proximo,
            "humor": humor, "fala": fala, "dormindo": dormindo,
            "dormindo_s": max(0, int(pet["dormindo_ate"] - agora)) if dormindo else 0,
            "brincar_em_s": max(0, espera),
            "encaixes": {a: cat.encaixe_acessorio(pet["especie"], a)
                         for a in cat.ENCAIXE_ACESSORIO} if pet["especie"] else {},
        }

    def pet(self):
        pet = self._pet_atualizado()
        return self._pet_publico(pet)

    def pet_batimento(self):
        """O app chama de tempos em tempos: marca que está aberto (o pet está acordado)."""
        with self.db:
            pet = self._pet_atualizado()
            pet["visto"] = self.agora()
            self._salvar_kv("pet", pet)

    def pet_chocar(self):
        pet = self._pet_atualizado()
        if pet["especie"]:
            raise ErroJogo("O ovo já chocou!")
        especie = self.rnd.choice(["slime", "galinha"])
        with self.db:
            pet.update(especie=especie, fome=80, alegria=90, energia=80, atualizado=self.agora())
            self._salvar_kv("pet", pet)
            self.db.execute("INSERT OR IGNORE INTO cartas VALUES (?, 1, 0)", (f"pet-{especie}",))
        return self._pet_publico(pet)

    def pet_acao(self, acao):
        pet = self._pet_atualizado()
        agora = self.agora()
        if not pet["especie"]:
            raise ErroJogo("Choque o ovo primeiro!")
        dormindo = pet["dormindo_ate"] and pet["dormindo_ate"] > agora
        if acao == "acordar":
            pet["dormindo_ate"] = None
        elif dormindo:
            raise ErroJogo(f"{_nome_do_pet(pet)} está dormindo. Shhh!")
        elif acao == "soneca":
            pet["dormindo_ate"] = agora + cat.PET_SONECA_MIN * 60
        elif acao == "alimentar":
            perfil = self._kv("perfil")
            if perfil["petiscos"] <= 0:
                raise ErroJogo("Sem petiscos! Compre na loja ou abra baús.")
            if pet["fome"] >= 98:
                raise ErroJogo(f"{_nome_do_pet(pet)} está cheio!")
            perfil["petiscos"] -= 1
            self._salvar_kv("perfil", perfil)
            self._aplicar(pet, cat.PET_ACOES["alimentar"])
        elif acao == "brincar":
            if agora - pet["ultimo_brincar"] < cat.PET_BRINCAR_ESPERA_MIN * 60:
                raise ErroJogo(f"{_nome_do_pet(pet)} ainda está cansado da última brincadeira.")
            if pet["energia"] < 15:
                raise ErroJogo(f"{_nome_do_pet(pet)} está sem energia. Que tal uma soneca?")
            pet["ultimo_brincar"] = agora
            self._aplicar(pet, cat.PET_ACOES["brincar"])
        else:
            raise ErroJogo("Ação desconhecida.")
        with self.db:
            self._salvar_kv("pet", pet)
        return self._pet_publico(pet)

    @staticmethod
    def _aplicar(pet, efeitos):
        for atributo, valor in efeitos.items():
            if atributo == "xp":
                pet["xp"] += valor
            else:
                pet[atributo] = max(0.0, min(100.0, pet[atributo] + valor))
