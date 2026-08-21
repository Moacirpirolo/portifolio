"""
Monta o painel do Rio Tiete: um HTML autonomo, sem CDN, com o rio no mapa,
o perfil dos 950 km e o estado de cada estacao automatica da CETESB.

Uso:
    python3 painel.py            # coleta tudo e gera rio_tiete.html
    python3 painel.py --cache    # usa dados_tiete.json e geo_tiete.json ja baixados
"""

import html
import json
import sys
from datetime import datetime

import coleta
import geo as geografia
import mapa as cartografia
from estilo import CSS

# Cada parametro com a regra que classifica o valor medido. So oxigenio,
# pH e turbidez tem padrao legal (CONAMA 357, agua doce classe 2); os outros
# entram como referencia tecnica e ficam sinalizados como tal.
PARAMETROS = [
    {
        "id": "oxigenio", "rotulo": "Oxigênio dissolvido", "curto": "Oxigênio",
        "unidade": "mg/L", "casas": 2, "limite": 5, "limite_texto": "5 mg/L, mínimo da classe 2",
        "fonte_regra": "Resolução CONAMA 357, água doce classe 2",
        "faixas": [
            {"ate": 2, "cor": "critico", "rotulo": "Sem vida aeróbica"},
            {"ate": 4, "cor": "ruim", "rotulo": "Ruim"},
            {"ate": 5, "cor": "atencao", "rotulo": "Abaixo da classe 2"},
            {"ate": 12, "cor": "bom", "rotulo": "Dentro do padrão"},
            {"ate": None, "cor": "excesso", "rotulo": "Supersaturado por algas"},
        ],
    },
    {
        "id": "turbidez", "rotulo": "Turbidez", "curto": "Turbidez",
        "unidade": "NTU", "casas": 1, "limite": 100, "limite_texto": "100 NTU, limite da classe 2",
        "fonte_regra": "Resolução CONAMA 357, água doce classe 2",
        "faixas": [
            {"ate": 40, "cor": "bom", "rotulo": "Água clara"},
            {"ate": 100, "cor": "atencao", "rotulo": "No limite"},
            {"ate": 200, "cor": "ruim", "rotulo": "Acima do padrão"},
            {"ate": None, "cor": "critico", "rotulo": "Muito acima"},
        ],
    },
    {
        "id": "ph", "rotulo": "pH", "curto": "pH",
        "unidade": "", "casas": 2, "limite": None, "limite_texto": "faixa de 6 a 9 na classe 2",
        "fonte_regra": "Resolução CONAMA 357, água doce classe 2",
        "faixas": [
            {"ate": 5, "cor": "critico", "rotulo": "Muito ácido"},
            {"ate": 6, "cor": "ruim", "rotulo": "Ácido demais"},
            {"ate": 9, "cor": "bom", "rotulo": "Dentro da faixa"},
            {"ate": None, "cor": "ruim", "rotulo": "Alcalino demais"},
        ],
    },
    {
        "id": "condutividade", "rotulo": "Condutividade elétrica", "curto": "Condutividade",
        "unidade": "µS/cm", "casas": 1, "limite": None,
        "limite_texto": "sem padrão legal; acima de 500 costuma indicar esgoto",
        "fonte_regra": "referência técnica, não há limite na CONAMA 357",
        "faixas": [
            {"ate": 100, "cor": "bom", "rotulo": "Baixa"},
            {"ate": 300, "cor": "atencao", "rotulo": "Moderada"},
            {"ate": 600, "cor": "ruim", "rotulo": "Alta"},
            {"ate": None, "cor": "critico", "rotulo": "Muito alta"},
        ],
    },
    {
        "id": "temperatura", "rotulo": "Temperatura da água", "curto": "Temperatura",
        "unidade": "°C", "casas": 1, "limite": None, "limite_texto": "sem classificação, valor de contexto",
        "fonte_regra": "informativo",
        "faixas": [{"ate": None, "cor": "neutro", "rotulo": "Medição"}],
    },
]


def esc(t):
    return html.escape(str(t), quote=True)


def num(v, casas=2):
    return "—" if v is None else f"{v:.{casas}f}".replace(".", ",")


def dt(texto):
    try:
        return datetime.strptime(texto.split(" ")[0], "%d/%m/%Y")
    except (ValueError, AttributeError):
        return None


def ultimo_com(registros, chave):
    for reg in reversed(registros):
        if reg.get(chave) is not None:
            return reg
    return None


def classificar(param, valor):
    if valor is None:
        return {"cor": "neutro", "rotulo": "Sem dado"}
    for faixa in param["faixas"]:
        if faixa["ate"] is None or valor <= faixa["ate"]:
            return {"cor": faixa["cor"], "rotulo": faixa["rotulo"]}
    return {"cor": "neutro", "rotulo": "Sem dado"}


# --------------------------------------------------------------- montagem

def preparar(dados, geo):
    """Organiza tudo que o JS precisa: series por parametro e ultimo valor."""
    rio = [tuple(p) for p in geo["tiete"]]
    agora = datetime.now()
    saida = []
    for est in dados["estacoes"]:
        km = None
        if est.get("lat") is not None:
            km = round(geo["km"][cartografia.indice_mais_proximo(rio, est["lon"], est["lat"])], 1)

        serie, hora, ultimo = {}, {}, {}
        for param in PARAMETROS:
            chave = param["id"]
            serie[chave] = [[r["data"], r.get(chave)] for r in est["diario"]]
            hora[chave] = [r.get(chave) for r in est["horario"]]
            reg = ultimo_com(est["diario"], chave)
            if reg:
                data_ref = dt(reg["data"])
                ultimo[chave] = {
                    "v": reg[chave], "data": reg["data"],
                    "idade": (agora - data_ref).days if data_ref else None,
                }
            else:
                ultimo[chave] = {"v": None, "data": None, "idade": None}

        saida.append({
            "codigo": est["codigo"], "nome": est["nome"], "municipio": est["municipio"],
            "trecho": est["trecho"], "km": km, "lat": est.get("lat"), "lon": est.get("lon"),
            "situacao": est.get("status_operacional", "—"),
            "validado_ate": est.get("validado_ate"),
            "datas_hora": [r["data"] for r in est["horario"]],
            "serie": serie, "hora": hora, "ultimo": ultimo,
        })
    return saida


def bloco_numeros(estacoes, dados):
    od = next(p for p in PARAMETROS if p["id"] == "oxigenio")
    por_codigo = {e["codigo"]: e for e in estacoes}
    def idade(est):
        valor = est["ultimo"]["oxigenio"]["idade"]
        return 999 if valor is None else valor

    vivas = [e for e in estacoes if idade(e) <= 2]

    def leitura(codigo):
        e = por_codigo.get(codigo, {})
        return e.get("ultimo", {}).get("oxigenio", {})

    penha, mogi, bb = leitura("EF29"), leitura("EF01"), leitura("EF35")
    cartoes = [
        ("critico", "Dentro da capital", f'{num(penha.get("v"))}<small> mg/L</small>',
         f'Estação da Penha, em {esc(penha.get("data") or "—")}. Abaixo de 2 mg/L a água não '
         f'sustenta vida aeróbica: é esgoto diluído correndo a céu aberto.'),
        ("bom", "Antes da capital", f'{num(mogi.get("v"))}<small> mg/L</small>',
         f'Estação de Mogi das Cruzes, {esc(mogi.get("data") or "—")}. A 60 km dali o mesmo rio '
         f'atende à classe 1 da CONAMA.'),
        ("bom", "500 km depois", f'{num(bb.get("v"))}<small> mg/L</small>',
         f'Barra Bonita, {esc(bb.get("data") or "—")}. Sem nenhuma estação de tratamento no meio '
         f'do caminho: quem despoluiu foi o próprio rio.'),
        ("atencao", "Estações transmitindo", f'{len(vivas)}<small> de {len(estacoes)}</small>',
         'Medição nas últimas 48 horas. O resto da rede está parada, em manutenção ou atrasada.'),
    ]
    return "".join(
        f'<div class="numero {cls}"><div class="rot">{esc(rot)}</div>'
        f'<div class="val">{val}</div><p class="exp">{exp}</p></div>'
        for cls, rot, val, exp in cartoes
    )


def bloco_cobertura(estacoes):
    linhas = []
    maior = max([(e["ultimo"]["oxigenio"]["idade"] or 90) for e in estacoes] + [1])
    for est in estacoes:
        info = est["ultimo"]["oxigenio"]
        idade = info["idade"]
        if idade is None:
            largura, cor, texto = 100, "critico", "sem dado no período"
        else:
            largura = max(3, min(100, idade / maior * 100))
            cor = "bom" if idade <= 2 else ("atencao" if idade <= 7 else "ruim")
            texto = "hoje" if idade == 0 else f"há {idade} dias"
        linhas.append(
            f'<div class="linha-cobertura">'
            f'<div><strong>{esc(est["codigo"])}</strong> {esc(est["nome"])}'
            f'<br><span class="km">{esc(est["situacao"])}</span></div>'
            f'<div class="barra-idade"><span style="width:{largura:.0f}%;background:var(--{cor})"></span></div>'
            f'<div class="quando">{esc(texto)}</div></div>'
        )
    return "".join(linhas)


def bloco_tabela(estacoes):
    cab = ["Estação", "Trecho", "km do rio"] + [p["curto"] for p in PARAMETROS] + ["Último dado", "Telemetria"]
    linhas = []
    for est in estacoes:
        celulas = []
        for param in PARAMETROS:
            info = est["ultimo"][param["id"]]
            estado = classificar(param, info["v"])
            celulas.append(
                f'<td class="n"><span style="color:var(--{estado["cor"]})">{num(info["v"], param["casas"])}</span></td>'
            )
        info_od = est["ultimo"]["oxigenio"]
        idade = info_od["idade"]
        viva = idade is not None and idade <= 2
        linhas.append(
            f'<tr><th scope="row">{esc(est["codigo"])} {esc(est["nome"])}</th>'
            f'<td>{esc(est["trecho"])}</td>'
            f'<td class="n">{num(est["km"], 0) if est["km"] else "—"}</td>'
            + "".join(celulas)
            + f'<td class="n">{esc(info_od["data"] or "—")}</td>'
            f'<td><span class="pill {"viva" if viva else "parada"}">'
            f'{"transmitindo" if viva else "parada"}</span></td></tr>'
        )
    return ('<table><thead><tr>' + "".join(f"<th>{esc(c)}</th>" for c in cab) +
            '</tr></thead><tbody>' + "".join(linhas) + '</tbody></table>')


JS = r"""
document.documentElement.classList.add("js");
const D = JSON.parse(document.getElementById("dados").textContent);
const SVGNS = "http://www.w3.org/2000/svg";
let atual = D.parametros[0];

const $ = (s, raiz = document) => raiz.querySelector(s);
const $$ = (s, raiz = document) => Array.from(raiz.querySelectorAll(s));
const fmt = (v, c) => v === null || v === undefined ? "—" : v.toFixed(c).replace(".", ",");
const cor = (nome) => `var(--${nome})`;

function param(id) { return D.parametros.find(p => p.id === id); }
function classificar(p, v) {
  if (v === null || v === undefined) return { cor: "neutro", rotulo: "Sem dado" };
  for (const f of p.faixas) if (f.ate === null || v <= f.ate) return f;
  return { cor: "neutro", rotulo: "Sem dado" };
}
function el(tag, attrs = {}, pai = null) {
  const n = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  if (pai) pai.appendChild(n);
  return n;
}

/* ------------------------------------------------------------- tooltip */
const tip = $("#tip");
function mostra(html, ev) {
  tip.innerHTML = html;
  tip.style.display = "block";
  const r = tip.getBoundingClientRect();
  let x = ev.clientX + 16, y = ev.clientY + 16;
  if (x + r.width > innerWidth - 10) x = ev.clientX - r.width - 16;
  if (y + r.height > innerHeight - 10) y = ev.clientY - r.height - 16;
  tip.style.left = x + "px"; tip.style.top = y + "px";
}
function esconde() { tip.style.display = "none"; }

/* ---------------------------------------------------------------- mapa */
function pintaMapa() {
  const p = atual;
  $$(".trecho").forEach(t => {
    const est = D.estacoes.find(e => e.codigo === t.dataset.estacao);
    const v = est ? est.ultimo[p.id].v : null;
    t.style.stroke = cor(classificar(p, v).cor);
  });
  $$(".pino").forEach(g => {
    const est = D.estacoes.find(e => e.codigo === g.dataset.estacao);
    if (!est) return;
    const info = est.ultimo[p.id];
    const c = classificar(p, info.v);
    $(".ponto", g).style.fill = cor(c.cor);
    const viva = info.idade !== null && info.idade <= 2;
    g.classList.toggle("viva", viva);
    g.classList.toggle("parada", !viva);
  });
}

function ligaMapa() {
  $$(".pino").forEach(g => {
    const codigo = g.dataset.estacao;
    const est = D.estacoes.find(e => e.codigo === codigo);
    const conta = (ev) => {
      const info = est.ultimo[atual.id];
      const c = classificar(atual, info.v);
      mostra(`<div class="tt">${est.codigo} · ${est.nome}</div>
        <div class="ts">km ${est.km} · ${est.municipio}</div>
        <div class="tl"><i style="background:${cor(c.cor)}"></i>
        ${atual.curto}: <strong>${fmt(info.v, atual.casas)} ${atual.unidade}</strong></div>
        <div class="ts">${c.rotulo} · medido em ${info.data || "—"}</div>`, ev);
      destaca(codigo);
    };
    g.addEventListener("mousemove", conta);
    g.addEventListener("mouseleave", () => { esconde(); destaca(null); });
    g.addEventListener("focus", () => destaca(codigo));
    g.addEventListener("blur", () => destaca(null));
    g.addEventListener("click", () => {
      const alvo = $(`#card-${codigo}`);
      if (alvo) alvo.scrollIntoView({ block: "center", behavior: "smooth" });
    });
  });
}

function destaca(codigo) {
  $$(".estacao").forEach(c => c.classList.toggle("destaque", c.id === `card-${codigo}`));
  $$(".pino").forEach(g => g.classList.toggle("aceso", g.dataset.estacao === codigo));
}

/* -------------------------------------------------- perfil longitudinal */
function desenhaPerfil() {
  const p = atual, L = 1000, A = 330;
  const esq = 58, dir = 26, topo = 26, base = 62;
  const pontos = D.estacoes.filter(e => e.km !== null && e.ultimo[p.id].v !== null)
    .map(e => ({ km: e.km, v: e.ultimo[p.id].v, est: e }))
    .sort((a, b) => a.km - b.km);
  const alvo = $("#perfil"); alvo.innerHTML = "";
  if (pontos.length < 2) { alvo.innerHTML = '<p class="nota">Sem medição suficiente.</p>'; return; }

  const svg = el("svg", { viewBox: `0 0 ${L} ${A}`, class: "grafico",
    role: "img", "aria-label": `${p.rotulo} ao longo do Rio Tietê` }, alvo);
  const vs = pontos.map(o => o.v);
  let lo = Math.min(0, ...vs), hi = Math.max(...vs) * 1.12;
  if (p.limite) hi = Math.max(hi, p.limite * 1.25);
  const kmMax = D.km_total;
  const X = km => esq + (km / kmMax) * (L - esq - dir);
  const Y = v => A - base - ((v - lo) / (hi - lo)) * (A - topo - base);

  for (let i = 0; i <= 4; i++) {
    const v = lo + (hi - lo) * i / 4;
    el("line", { class: "grade", x1: esq, y1: Y(v), x2: L - dir, y2: Y(v) }, svg);
    const t = el("text", { class: "tick", x: esq - 9, y: Y(v) + 4, "text-anchor": "end" }, svg);
    t.textContent = fmt(v, v > 20 ? 0 : 1);
  }
  const un = el("text", { class: "tick", x: esq - 9, y: topo - 8, "text-anchor": "end" }, svg);
  un.textContent = p.unidade;

  if (p.limite) {
    el("line", { class: "limite", x1: esq, y1: Y(p.limite), x2: L - dir, y2: Y(p.limite) }, svg);
    const t = el("text", { class: "tick-limite", x: L - dir, y: Y(p.limite) - 8, "text-anchor": "end" }, svg);
    t.textContent = p.limite_texto;
  }

  el("line", { class: "base", x1: esq, y1: A - base, x2: L - dir, y2: A - base }, svg);
  for (let km = 0; km <= kmMax - 120; km += 100) {
    const t = el("text", { class: "tick", x: X(km), y: A - base + 18, "text-anchor": "middle" }, svg);
    t.textContent = km === 0 ? "nascente" : km;
  }
  const foz = el("text", { class: "tick", x: L - dir, y: A - base + 18, "text-anchor": "end" }, svg);
  foz.textContent = "foz · km " + Math.round(kmMax);

  // area sob a linha, em degrade pelas faixas de qualidade
  const d = pontos.map((o, i) => `${i ? "L" : "M"}${X(o.km).toFixed(1)} ${Y(o.v).toFixed(1)}`).join("");
  const area = `${d}L${X(pontos[pontos.length - 1].km).toFixed(1)} ${A - base}L${X(pontos[0].km).toFixed(1)} ${A - base}Z`;
  el("path", { class: "area", d: area, fill: "var(--acento)" }, svg);
  el("path", { class: "linha", d, stroke: "var(--acento)" }, svg);

  pontos.forEach(o => {
    const c = classificar(p, o.v);
    const g = el("g", { class: "pt-perfil", tabindex: "0" }, svg);
    el("circle", { class: "ponta", cx: X(o.km), cy: Y(o.v), r: 6.5, fill: cor(c.cor) }, g);
    const rot = el("text", { class: "rotulo-serie", x: X(o.km),
      y: Y(o.v) > A - base - 34 ? Y(o.v) - 14 : Y(o.v) - 14, "text-anchor": "middle",
      fill: "var(--ink)" }, g);
    rot.textContent = o.est.codigo;
    const baixo = Y(o.v) > A - base - 34;
    const val = el("text", { class: "rotulo-serie", x: X(o.km),
      y: baixo ? Y(o.v) - 27 : Y(o.v) + 21, "text-anchor": "middle", fill: "var(--ink-2)" }, g);
    val.textContent = fmt(o.v, p.casas);
    const conta = (ev) => {
      mostra(`<div class="tt">${o.est.codigo} · ${o.est.nome}</div>
        <div class="ts">km ${o.km} do rio · ${o.est.municipio}</div>
        <div class="tl"><i style="background:${cor(c.cor)}"></i>
        ${atual.curto}: <strong>${fmt(o.v, p.casas)} ${p.unidade}</strong></div>
        <div class="ts">${c.rotulo} · ${o.est.ultimo[p.id].data}</div>`, ev);
      destaca(o.est.codigo);
    };
    g.addEventListener("mousemove", conta);
    g.addEventListener("mouseleave", () => { esconde(); destaca(null); });
  });
}

/* ------------------------------------------------------------- cartoes */
function desenhaCartoes() {
  const p = atual;
  D.estacoes.forEach(est => {
    const card = $(`#card-${est.codigo}`);
    if (!card) return;
    const info = est.ultimo[p.id];
    const c = classificar(p, info.v);
    card.style.setProperty("--cor-estado", cor(c.cor));
    $(".n", card).innerHTML = `${fmt(info.v, p.casas)} <small>${p.unidade}</small>`;
    $(".estado", card).textContent = c.rotulo;
    $(".quando", card).textContent = info.data
      ? `medido em ${info.data}` : `sem medição de ${p.curto.toLowerCase()} no período`;
    desenhaSpark($(".faixa-spark", card), est.serie[p.id], p, c);
    const vals = est.serie[p.id].map(x => x[1]).filter(v => v !== null);
    $(".rodape-spark", card).innerHTML = vals.length
      ? `<span>mín ${fmt(Math.min(...vals), p.casas)}</span><span>${D.dias_diario} dias</span>` +
        `<span>máx ${fmt(Math.max(...vals), p.casas)}</span>`
      : "";
  });
}

function desenhaSpark(alvo, serie, p, estado) {
  alvo.innerHTML = "";
  const L = 300, A = 62, pad = 5;
  const svg = el("svg", { viewBox: `0 0 ${L} ${A}`, class: "grafico" }, alvo);
  const vals = serie.map(x => x[1]);
  const validos = vals.filter(v => v !== null);
  if (validos.length < 2) return;
  let lo = Math.min(...validos), hi = Math.max(...validos);
  if (hi - lo < 1e-6) { lo -= 0.5; hi += 0.5; }
  const X = i => pad + i * (L - 2 * pad) / (vals.length - 1);
  const Y = v => A - pad - (v - lo) / (hi - lo) * (A - 2 * pad);

  if (p.limite && p.limite >= lo && p.limite <= hi) {
    el("line", { class: "limite", x1: 0, y1: Y(p.limite), x2: L, y2: Y(p.limite) }, svg);
  }
  let d = "", aberto = false, ultimo = null;
  vals.forEach((v, i) => {
    if (v === null) { aberto = false; return; }
    d += `${aberto ? "L" : "M"}${X(i).toFixed(1)} ${Y(v).toFixed(1)}`;
    aberto = true; ultimo = [X(i), Y(v)];
  });
  el("path", { class: "linha", d, stroke: "var(--acento)" }, svg);
  if (ultimo) el("circle", { class: "ponta", cx: ultimo[0], cy: ultimo[1], r: 4.5,
    fill: cor(estado.cor) }, svg);

  const area = el("rect", { x: 0, y: 0, width: L, height: A, fill: "transparent" }, svg);
  area.addEventListener("mousemove", ev => {
    const caixa = svg.getBoundingClientRect();
    const i = Math.round((ev.clientX - caixa.left) / caixa.width * (vals.length - 1));
    const v = vals[Math.max(0, Math.min(vals.length - 1, i))];
    mostra(`<div class="ts">${serie[i] ? serie[i][0] : ""}</div>
      <div class="tl"><strong>${fmt(v, p.casas)} ${p.unidade}</strong></div>`, ev);
  });
  area.addEventListener("mouseleave", esconde);
}

/* ------------------------------------------------------- serie horaria */
function desenhaHorario() {
  const p = atual, L = 1000, A = 340;
  const esq = 58, dir = 66, topo = 30, base = 48;
  const alvo = $("#horario"); alvo.innerHTML = "";
  const vivas = D.estacoes.filter(e => e.hora[p.id].filter(v => v !== null).length > 5);
  const legenda = $("#legenda-horario"); legenda.innerHTML = "";
  if (!vivas.length) {
    alvo.innerHTML = '<p class="nota">Nenhuma estação transmitindo este parâmetro agora.</p>';
    return;
  }
  const datas = vivas[0].datas_hora, n = datas.length;
  const todos = vivas.flatMap(e => e.hora[p.id]).filter(v => v !== null);
  let lo = Math.min(...todos), hi = Math.max(...todos);
  const folga = (hi - lo) * 0.12 || 0.5;
  lo = Math.max(0, lo - folga); hi = hi + folga;
  const X = i => esq + i * (L - esq - dir) / (n - 1);
  const Y = v => A - base - (v - lo) / (hi - lo) * (A - topo - base);

  const svg = el("svg", { viewBox: `0 0 ${L} ${A}`, class: "grafico", role: "img",
    "aria-label": `${p.rotulo} hora a hora` }, alvo);
  for (let i = 0; i <= 4; i++) {
    const v = lo + (hi - lo) * i / 4;
    el("line", { class: "grade", x1: esq, y1: Y(v), x2: L - dir, y2: Y(v) }, svg);
    const t = el("text", { class: "tick", x: esq - 9, y: Y(v) + 4, "text-anchor": "end" }, svg);
    t.textContent = fmt(v, 1);
  }
  const un = el("text", { class: "tick", x: esq - 9, y: topo - 10, "text-anchor": "end" }, svg);
  un.textContent = p.unidade;
  if (p.limite && p.limite >= lo && p.limite <= hi) {
    el("line", { class: "limite", x1: esq, y1: Y(p.limite), x2: L - dir, y2: Y(p.limite) }, svg);
    const t = el("text", { class: "tick-limite", x: L - dir - 8, y: Y(p.limite) - 9,
      "text-anchor": "end" }, svg);
    t.textContent = p.limite_texto;
  }
  el("line", { class: "base", x1: esq, y1: A - base, x2: L - dir, y2: A - base }, svg);
  const passo = Math.max(1, Math.round(n / 7));
  for (let i = 0; i < n; i += passo) {
    const t = el("text", { class: "tick", x: X(i), y: A - base + 18, "text-anchor": "middle" }, svg);
    t.textContent = datas[i].slice(0, 5);
  }

  const series = [];
  const usados = [];
  vivas.slice(0, 3).forEach((est, idx) => {
    const traco = `var(--serie-${idx + 1})`;
    const vals = est.hora[p.id];
    let d = "", aberto = false, fim = null;
    vals.forEach((v, i) => {
      if (v === null) { aberto = false; return; }
      d += `${aberto ? "L" : "M"}${X(i).toFixed(1)} ${Y(v).toFixed(1)}`;
      aberto = true; fim = [X(i), Y(v)];
    });
    el("path", { class: "linha", d, stroke: traco }, svg);
    if (fim) {
      el("circle", { class: "ponta", cx: fim[0], cy: fim[1], r: 4.5, fill: traco }, svg);
      let y = fim[1] + 4;
      while (usados.some(u => Math.abs(u - y) < 16)) y += 16;
      usados.push(y);
      const t = el("text", { class: "rotulo-serie", x: fim[0] + 9, y, fill: traco }, svg);
      t.textContent = est.codigo;
    }
    series.push({ est, traco, vals });
    legenda.insertAdjacentHTML("beforeend",
      `<span class="chip"><i style="background:${traco}"></i>${est.codigo} · ${est.nome}</span>`);
  });

  const cursor = el("line", { class: "grade", x1: 0, y1: topo, x2: 0, y2: A - base,
    style: "display:none;stroke:var(--linha-forte)" }, svg);
  const area = el("rect", { x: esq, y: topo, width: L - esq - dir, height: A - topo - base,
    fill: "transparent" }, svg);
  area.addEventListener("mousemove", ev => {
    const caixa = svg.getBoundingClientRect();
    const xv = (ev.clientX - caixa.left) / caixa.width * L;
    const frac = Math.min(1, Math.max(0, (xv - esq) / (L - esq - dir)));
    const i = Math.round(frac * (n - 1));
    cursor.setAttribute("x1", X(i)); cursor.setAttribute("x2", X(i));
    cursor.style.display = "block";
    mostra(`<div class="ts">${datas[i]}</div>` + series.map(s =>
      `<div class="tl"><i style="background:${s.traco}"></i>${s.est.codigo}:
       <strong>${fmt(s.vals[i], p.casas)} ${p.unidade}</strong></div>`).join(""), ev);
  });
  area.addEventListener("mouseleave", () => { cursor.style.display = "none"; esconde(); });
}

/* --------------------------------------------------------------- farol */
const ORDEM = ["critico", "ruim", "excesso", "atencao", "bom", "neutro"];
const minusculo = (p) => p.id === "ph" ? "pH" : p.rotulo.toLowerCase();

function desenhaFarol() {
  const p = atual;
  const grupos = new Map();
  D.estacoes.forEach(est => {
    const info = est.ultimo[p.id];
    const chave = info.v === null ? "sem" : classificar(p, info.v).cor;
    if (!grupos.has(chave)) grupos.set(chave, []);
    grupos.get(chave).push({ est, info, faixa: classificar(p, info.v) });
  });

  // o farol acende pela pior condicao medida, como em qualquer painel de estado
  const pior = ORDEM.find(c => grupos.has(c));
  const lista = pior ? grupos.get(pior) : [];
  const referencia = lista.length
    ? lista.slice().sort((a, b) => (a.info.idade ?? 999) - (b.info.idade ?? 999))[0]
    : null;
  const acesa = pior || "sem";

  // tres luzes: alerta em cima, atencao no meio, tudo certo embaixo.
  // a luz acesa recebe a cor exata do estado medido.
  const posicao = { critico: 0, ruim: 0, excesso: 1, atencao: 1, bom: 2, neutro: -1, sem: -1 };
  const base = ["critico", "atencao", "bom"];
  $("#luzes").innerHTML = base.map((c, i) => {
    const ligada = posicao[acesa] === i;
    const tom = ligada ? cor(acesa) : cor(c);
    return `<span class="luz ${ligada ? "acesa" : ""}" style="--luz:${tom}"></span>`;
  }).join("");
  $("#farol").dataset.estado = acesa;
  $("#farol").style.setProperty("--cor-farol", cor(acesa === "sem" ? "neutro" : acesa));

  const transmitindo = D.estacoes.filter(e => (e.ultimo[p.id].idade ?? 999) <= 2).length;

  if (!referencia) {
    $("#farol-frase").textContent = "Sem medição recente para este parâmetro.";
    $("#farol-detalhe").textContent = "";
  } else if (acesa === "neutro") {
    // parametro sem classificacao legal: o farol informa a amplitude medida
    const medidos = D.estacoes.map(e => e.ultimo[p.id].v).filter(v => v !== null);
    $("#farol-frase").innerHTML =
      `${minusculo(p)} <span class="fino">de ${fmt(Math.min(...medidos), p.casas)} a ` +
      `${fmt(Math.max(...medidos), p.casas)} ${p.unidade} ao longo do rio</span>`;
    $("#farol-detalhe").textContent =
      `Este parâmetro não tem faixa de classificação na CONAMA 357: entra como contexto. ` +
      `${transmitindo} de ${D.estacoes.length} estações transmitiram nas últimas 48 horas.`;
    const semDado = D.estacoes.filter(e => e.ultimo[p.id].v === null).length;
    $("#farol-contagem").innerHTML = semDado
      ? `<span class="conta"><i style="background:${cor("neutro")}"></i>
         <strong>${semDado}</strong> sem medição</span>` : "";
    return;
  } else {
    const nomes = lista.length > 1
      ? `em ${lista.length} das ${D.estacoes.length} estações`
      : `na estação ${referencia.est.codigo}, em ${referencia.est.municipio}`;
    $("#farol-frase").innerHTML =
      `${referencia.faixa.rotulo.toLowerCase()} <span class="fino">${nomes}</span>`;
    $("#farol-detalhe").textContent =
      `Pior leitura de ${minusculo(p)}: ${fmt(referencia.info.v, p.casas)} ${p.unidade} ` +
      `em ${referencia.est.codigo} ${referencia.est.nome}, medido em ${referencia.info.data}. ` +
      `O farol acende pelo pior trecho medido, com ${transmitindo} de ${D.estacoes.length} ` +
      `estações transmitindo nas últimas 48 horas.`;
  }

  const ordemContagem = [...ORDEM, "sem"];
  $("#farol-contagem").innerHTML = ordemContagem.filter(c => grupos.has(c)).map(c => {
    const g = grupos.get(c);
    const rotulo = c === "sem" ? "sem medição" : g[0].faixa.rotulo.toLowerCase();
    if (c === "neutro") return "";
    return `<span class="conta"><i style="background:${cor(c === "sem" ? "neutro" : c)}"></i>
      <strong>${g.length}</strong> ${rotulo}</span>`;
  }).join("");
}

/* --------------------------------------------------------------- ligar */
function trocaParametro(id) {
  atual = param(id);
  $$(".opcoes button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.param === id)));
  $("#regra").textContent = atual.fonte_regra;
  $$(".titulo-param").forEach(t => t.textContent = atual.rotulo.toLowerCase());
  $("#dica-pulso").textContent = atual.id === "oxigenio"
    ? "É aqui que aparece o ciclo diário: o oxigênio sobe de tarde, quando as algas fazem fotossíntese, e cai de madrugada."
    : (atual.id === "turbidez"
       ? "Os picos coincidem com chuva: a enxurrada leva terra e lixo para dentro do rio."
       : "Passe o mouse para ler hora a hora.");
  desenhaFarol(); pintaMapa(); desenhaPerfil(); desenhaCartoes(); desenhaHorario(); montaLegendaMapa();
}

function montaLegendaMapa() {
  const alvo = $("#legenda-mapa");
  let piso = null;
  alvo.innerHTML = atual.faixas.map(f => {
    let limite;
    if (f.ate === null) limite = piso === null ? "qualquer valor" : `acima de ${fmt(piso, 0)}`;
    else if (piso === null) limite = `até ${fmt(f.ate, 0)}`;
    else limite = `${fmt(piso, 0)} a ${fmt(f.ate, 0)}`;
    piso = f.ate;
    return `<span><i style="background:${cor(f.cor)}"></i>${f.rotulo}
      <span style="color:var(--ink-3)">(${limite} ${atual.unidade})</span></span>`;
  }).join("") +
  `<span><i style="background:var(--neutro)"></i>Sem medição
    <span style="color:var(--ink-3)">(estação parada ou em manutenção)</span></span>`;
}

$$(".opcoes button").forEach(b =>
  b.addEventListener("click", () => trocaParametro(b.dataset.param)));

if ("IntersectionObserver" in window) {
  const obs = new IntersectionObserver(entradas => {
    entradas.forEach(e => { if (e.isIntersecting) { e.target.classList.add("visivel"); obs.unobserve(e.target); } });
  }, { threshold: 0.02, rootMargin: "0px 0px -5% 0px" });
  $$(".revela").forEach(n => obs.observe(n));
} else {
  $$(".revela").forEach(n => n.classList.add("visivel"));
}

ligaMapa();
trocaParametro(D.parametros[0].id);
addEventListener("resize", () => { desenhaPerfil(); desenhaHorario(); desenhaCartoes(); });
"""


def montar_html(dados, geo):
    estacoes = preparar(dados, geo)
    svg_geral, meta_geral = cartografia.montar(
        geo, dados["estacoes"], largura=1000, altura=470, prefixo="g",
        margem={"esq": 34, "dir": 34, "topo": 46, "base": 92},
        anotacoes=[{"lon": -46.75, "lat": -23.52, "dx": -150, "dy": 58, "anc": "end",
                    "texto": "quatro estações espremidas|nos primeiros 200 km"}])
    faixa = cartografia.faixa_metropolitana(geo, dados["estacoes"])
    svg_metro, _ = cartografia.montar(
        geo, dados["estacoes"], faixa=faixa, largura=560, altura=340,
        margem={"esq": 44, "dir": 44, "topo": 62, "base": 58},
        rotulos=cartografia.ROTULOS_METRO, com_estado=False, prefixo="m", marcos=False)

    payload = {
        "gerado_em": dados["gerado_em"],
        "dias_diario": dados["dias_diario"],
        "km_total": meta_geral["km_fim"],
        "parametros": PARAMETROS,
        "estacoes": estacoes,
    }

    botoes = "".join(
        f'<button type="button" data-param="{p["id"]}" aria-pressed="false">{esc(p["curto"])}</button>'
        for p in PARAMETROS
    )

    cartoes = "".join(
        f'<article class="estacao" id="card-{esc(est["codigo"])}">'
        f'<div class="km">km {num(est["km"], 0) if est["km"] else "—"} · {esc(est["trecho"])}</div>'
        f'<div class="nome">{esc(est["codigo"])} {esc(est["nome"])}</div>'
        f'<div class="local">{esc(est["municipio"])}</div>'
        f'<div class="leitura"><div class="n">—</div><div class="estado">—</div></div>'
        f'<div class="faixa-spark"></div>'
        f'<div class="rodape-spark"></div>'
        f'<div class="km quando" style="margin-top:6px"></div>'
        f'</article>'
        for est in estacoes
    )

    validados = sorted({e["validado_ate"].split(" ")[0] for e in estacoes if e.get("validado_ate")})
    validado_txt = ", ".join(validados) if validados else "não informado"

    km_txt = num(meta_geral["km_fim"], 0)
    numeros = bloco_numeros(estacoes, dados)

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rio Tietê em tempo real</title>
<meta name="description" content="O Rio Tietê medido pelas estações automáticas da CETESB, da nascente à foz.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;700;800&family=IBM+Plex+Mono:wght@400;500&family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap">
<style>{CSS}</style>
</head>
<body>
<div class="faixa-topo"></div>
<div class="envelope">

<section class="farol" id="farol" aria-live="polite">
  <div class="luzes" id="luzes" role="img" aria-label="Estado geral do rio"></div>
  <div class="veredito">
    <span class="eyebrow">O Tietê agora</span>
    <p class="frase" id="farol-frase">—</p>
    <p class="detalhe" id="farol-detalhe">—</p>
  </div>
  <div class="contagem" id="farol-contagem"></div>
</section>

<header class="capa">
  <span class="eyebrow">Estações automáticas da CETESB · leitura a cada 5 minutos</span>
  <h1>O mesmo rio, <em>três rios diferentes</em> em 950 quilômetros</h1>
  <p class="linha-fina">O Tietê nasce em Salesópolis com água de classe 1, morre asfixiado
  ao atravessar São Paulo e volta a respirar sozinho 400 km depois. Não é opinião: são as sondas
  da CETESB medindo oxigênio, pH, turbidez, condutividade e temperatura a cada cinco minutos,
  com os dados abertos a qualquer um. Este painel lê essa telemetria direto da fonte.</p>
  <div class="assinatura">
    <span><i class="ponto"></i>gerado em {esc(dados["gerado_em"])}</span>
    <span>fonte: SIMQUA/CETESB · traçado do rio: ANA/SNIRH · contorno: IBGE</span>
    <span>dado validado pela CETESB até {esc(validado_txt)}</span>
  </div>
</header>

<div class="barra">
  <div class="opcoes" role="group" aria-label="Parâmetro medido">{botoes}</div>
  <div class="aviso">critério: <span id="regra"></span></div>
</div>

<section id="mapa" class="revela">
  <div class="moldura-mapa principal">
    <span class="rotulo-mapa">Rio Tietê · da nascente em Salesópolis à foz no rio Paraná · {km_txt} km</span>
    {svg_geral}
  </div>
  <div class="legenda-mapa" id="legenda-mapa"></div>

  <div class="apoio-mapa">
    <div class="moldura-mapa">
      <span class="rotulo-mapa">Detalhe · Alto Tietê</span>
      {svg_metro}
    </div>
    <div class="explica">
      <h2>O rio pintado pelo que as sondas medem</h2>
      <p class="nota">Cada trecho recebe a cor da estação mais próxima. Passe o mouse nos pontos
      para ver a medição, ou troque o parâmetro na barra acima. O detalhe ao lado abre os primeiros
      200 km, onde quatro estações se espremem entre a nascente e a saída da região metropolitana:
      é nesse pedaço curto que o rio sai de classe 1 para esgoto a céu aberto.</p>
      <p class="nota">Ponto cheio é estação transmitindo. Ponto vazado é estação parada, e nesse
      caso a cor do trecho é a última medição conhecida, não a de hoje.</p>
    </div>
  </div>

  <div class="numeros">{numeros}</div>
</section>

<section id="perfil-secao" class="revela">
  <header>
    <span class="eyebrow">perfil longitudinal</span>
    <h2>Os 950 km em uma linha só</h2>
    <p class="nota">Cada ponto é uma estação, posicionada pela distância real ao longo do rio.
    A leitura é de <span class="titulo-param">oxigênio dissolvido</span>.</p>
  </header>
  <div class="cartao tela"><div id="perfil"></div></div>
</section>

<section id="estacoes" class="revela">
  <header>
    <span class="eyebrow">estação por estação</span>
    <h2>Da nascente para a foz</h2>
    <p class="nota">Último valor medido e a série dos últimos {dados["dias_diario"]} dias.
    Trecho vazio na linha significa estação sem medição no período.</p>
  </header>
  <div class="escada">{cartoes}</div>
</section>

<section id="pulso" class="revela">
  <header>
    <span class="eyebrow">últimos dias, hora a hora</span>
    <h2>O pulso de quem ainda transmite</h2>
    <p class="nota">Média horária de <span class="titulo-param">oxigênio dissolvido</span> nas
    estações com transmissão ativa. <span id="dica-pulso"></span></p>
  </header>
  <div class="cartao tela">
    <div class="legenda" id="legenda-horario"></div>
    <div id="horario"></div>
  </div>
</section>

<section id="cobertura" class="revela">
  <header>
    <span class="eyebrow">a telemetria por trás do painel</span>
    <h2>Metade da rede está muda</h2>
    <p class="nota">Um painel de rio tem o mesmo problema de qualquer painel de infraestrutura:
    o número parece atual até você perguntar de quando ele é. Esta é a idade do último dado de
    cada estação. Sem essa camada, o painel mostraria medição de três semanas atrás como se fosse de hoje.</p>
  </header>
  <div class="cartao tela cobertura">{bloco_cobertura(estacoes)}</div>
</section>

<section id="tabela" class="revela">
  <header>
    <span class="eyebrow">tudo junto</span>
    <h2>Última medição válida de cada estação</h2>
  </header>
  <div class="cartao tela rolagem">{bloco_tabela(estacoes)}</div>
</section>

<footer class="creditos">
  <div>
    <h3>De onde vêm os dados</h3>
    <p>Medições: SIMQUA/CETESB, endpoint público <code>/dados/</code>, sem autenticação.
    Traçado do rio e afluentes: Base Hidrográfica Ottocodificada 2017 da ANA/SNIRH.
    Contorno do estado: malha territorial do IBGE.</p>
  </div>
  <div>
    <h3>Como ler os valores</h3>
    <p>Oxigênio dissolvido acima de 5 mg/L é o mínimo da classe 2 na Resolução CONAMA 357.
    Acima de 12 mg/L costuma ser supersaturação por floração de algas, não água melhor.
    Condutividade não tem limite legal: entra como referência técnica.</p>
  </div>
  <div>
    <h3>Ressalvas</h3>
    <p>Valores mais recentes que a data de validação ainda passam por consistência técnica da
    CETESB e podem mudar. A cor de cada trecho no mapa é a da estação mais próxima, não uma
    medição contínua do rio inteiro.</p>
  </div>
</footer>

</div>
<div class="tip" id="tip"></div>
<script type="application/json" id="dados">{json.dumps(payload, ensure_ascii=False)}</script>
<script>{JS}</script>
</body>
</html>
"""


if __name__ == "__main__":
    usar_cache = "--cache" in sys.argv
    if usar_cache:
        dados = json.load(open("dados_tiete.json", encoding="utf-8"))
        geo = json.load(open("geo_tiete.json", encoding="utf-8"))
        print("usando dados_tiete.json e geo_tiete.json")
    else:
        print("medições (SIMQUA/CETESB):")
        dados = coleta.coletar()
        json.dump(dados, open("dados_tiete.json", "w", encoding="utf-8"), ensure_ascii=False)
        print("geometria (ANA/SNIRH e IBGE):")
        geo = geografia.baixar()
        json.dump(geo, open("geo_tiete.json", "w", encoding="utf-8"))

    with open("rio_tiete.html", "w", encoding="utf-8") as f:
        f.write(montar_html(dados, geo))
    print("rio_tiete.html gerado")
