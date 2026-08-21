CSS = """
/* ---------------------------------------------------------------- tokens
   A pagina assume um so tema: papel branco. O rio e o unico elemento com
   cor forte, tudo em volta e recuado de proposito. */
:root {
  color-scheme: light;

  --papel:        #ffffff;
  --superficie:   #ffffff;
  --superficie-2: #ffffff;
  --cartao:       #f7fafb;
  --agua-fundo:   #eaf2f5;   /* papel do mapa */
  --agua-terra:   #f2f6f7;   /* massa de terra dentro do mapa */

  --ink:   #0c1a20;
  --ink-2: #465a61;
  --ink-3: #8598a0;
  --linha: #e2eaec;
  --linha-forte: #c3d2d6;

  --acento:      #12667f;
  --acento-forte:#0a4457;
  --acento-suave: rgba(18,102,127,0.08);

  --bom:      #0f8f2f;
  --atencao:  #b07d00;
  --ruim:     #d1673a;
  --critico:  #c22f2f;
  --neutro:   #9fb0b6;
  --excesso:  #6a5acd;

  --sombra: 0 1px 2px rgba(12,26,32,.04), 0 14px 34px -22px rgba(12,26,32,.30);
  --raio: 14px;
  --serie-1: #12667f;
  --serie-2: #d1673a;
  --serie-3: #0f8f2f;
}

/* ------------------------------------------------------------- estrutura */
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--papel);
  color: var(--ink);
  font-family: Newsreader, Georgia, "Times New Roman", serif;
  font-size: 17px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
.faixa-topo {
  height: 4px;
  background: linear-gradient(90deg, var(--critico) 0 8%, var(--ruim) 8% 18%,
    var(--atencao) 18% 26%, var(--acento) 26% 62%, var(--bom) 62% 100%);
}
.envelope { max-width: 1180px; margin: 0 auto; padding: 0 24px 96px; }

h1, h2, h3, .display {
  font-family: Archivo, "Helvetica Neue", Arial, sans-serif;
  font-weight: 700;
  letter-spacing: -0.02em;
  text-wrap: balance;
  margin: 0;
}
.mono, .eyebrow, .km, .tick, .valor, td.n, .pill, .chip, thead th {
  font-family: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}
.eyebrow {
  font-size: 11.5px; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--ink-3); display: block; margin-bottom: 10px;
}

/* ----------------------------------------------------------------- farol
   Estado do rio pelo pior trecho medido, como em qualquer pagina de status. */
.farol {
  margin-top: 28px; padding: 22px 26px;
  display: grid; gap: 18px 26px; align-items: center;
  grid-template-columns: auto minmax(0, 1fr);
  border: 1px solid var(--linha); border-left: 5px solid var(--cor-farol, var(--neutro));
  border-radius: var(--raio);
  background: linear-gradient(90deg,
    color-mix(in srgb, var(--cor-farol, var(--neutro)) 7%, transparent),
    transparent 42%);
}
@media (min-width: 860px) { .farol { grid-template-columns: auto minmax(0, 1fr) auto; } }

.luzes {
  display: flex; flex-direction: column; gap: 9px; padding: 13px 14px;
  border: 1px solid var(--linha); border-radius: 999px; background: var(--superficie);
}
.luz {
  width: 19px; height: 19px; border-radius: 50%;
  background: color-mix(in srgb, var(--luz) 14%, var(--linha));
  border: 1px solid color-mix(in srgb, var(--luz) 26%, transparent);
}
.luz.acesa {
  background: var(--luz); border-color: var(--luz);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--luz) 18%, transparent);
  animation: pulsar 2.4s ease-in-out infinite;
}
@keyframes pulsar {
  0%, 100% { box-shadow: 0 0 0 4px color-mix(in srgb, var(--luz) 18%, transparent); }
  50% { box-shadow: 0 0 0 8px color-mix(in srgb, var(--luz) 6%, transparent); }
}
.veredito .frase {
  font-family: Archivo, sans-serif; font-weight: 700; letter-spacing: -0.02em;
  font-size: clamp(21px, 2.6vw, 31px); line-height: 1.12; margin: 0;
  color: var(--cor-farol, var(--ink)); text-wrap: balance;
}
.veredito .frase .fino { color: var(--ink); font-weight: 500; }
.veredito .detalhe {
  margin: 8px 0 0; color: var(--ink-2); font-size: 15px; max-width: 62ch;
  font-family: Newsreader, Georgia, serif;
}
.contagem { display: flex; flex-wrap: wrap; gap: 8px 16px; }
@media (min-width: 860px) { .contagem { flex-direction: column; gap: 8px; } }
.conta {
  display: inline-flex; align-items: center; gap: 8px; white-space: nowrap;
  font-family: "IBM Plex Mono", monospace; font-size: 12.5px; color: var(--ink-2);
}
.conta i { width: 10px; height: 10px; border-radius: 3px; flex: none; }
.conta strong { color: var(--ink); font-weight: 500; }

/* ------------------------------------------------------------------ capa */
.capa { padding: 34px 0 34px; }
.capa h1 {
  font-size: clamp(38px, 6.4vw, 76px);
  line-height: 0.98;
  font-stretch: 112%;
  max-width: 16ch;
}
.capa h1 em { font-style: normal; color: var(--acento); }
.capa .linha-fina {
  margin: 22px 0 0; max-width: 62ch; font-size: clamp(17px, 1.5vw, 20px);
  color: var(--ink-2);
}
.assinatura {
  margin-top: 20px; display: flex; flex-wrap: wrap; gap: 8px 18px;
  font-family: "IBM Plex Mono", monospace; font-size: 12px; color: var(--ink-3);
}
.assinatura span { display: inline-flex; align-items: center; gap: 6px; }
.assinatura .ponto { width: 6px; height: 6px; border-radius: 50%; background: var(--acento); }

/* ------------------------------------------------------------- destaques */
.numeros {
  display: grid; gap: 1px; margin-top: 34px;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  background: var(--linha); border: 1px solid var(--linha); border-radius: var(--raio);
  overflow: hidden;
}
.numero { background: var(--cartao); padding: 20px 22px 22px; }
.numero .rot { font-family: "IBM Plex Mono", monospace; font-size: 11px;
  letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-3); }
.numero .val {
  font-family: Archivo, sans-serif; font-weight: 700; font-size: 42px;
  line-height: 1.05; margin: 10px 0 6px; font-variant-numeric: tabular-nums;
  letter-spacing: -0.03em;
}
.numero .val small { font-size: 15px; font-weight: 500; color: var(--ink-2); letter-spacing: 0; }
.numero .exp { font-size: 14.5px; color: var(--ink-2); line-height: 1.45; }
.numero.bom .val { color: var(--bom); }
.numero.critico .val { color: var(--critico); }
.numero.atencao .val { color: var(--atencao); }

/* --------------------------------------------------------------- secoes */
section { margin-top: 76px; scroll-margin-top: 84px; }
#mapa { margin-top: 0; }
section > header { max-width: 68ch; margin-bottom: 22px; }
section h2 { font-size: clamp(24px, 3vw, 34px); line-height: 1.1; }
section .nota { margin: 12px 0 0; color: var(--ink-2); font-size: 16.5px;
  font-family: Newsreader, Georgia, "Times New Roman", serif; }
.cartao {
  background: var(--cartao); border: 1px solid var(--linha);
  border-radius: var(--raio); box-shadow: var(--sombra);
}
.cartao.tela { padding: 22px; }

/* ------------------------------------------------------------ parametros */
.barra {
  position: sticky; top: 0; z-index: 20; margin: 0 -24px 26px;
  padding: 10px 24px; display: flex; flex-wrap: wrap; gap: 10px 14px;
  align-items: center; justify-content: space-between;
  background: color-mix(in srgb, var(--papel) 86%, transparent);
  backdrop-filter: blur(10px); border-bottom: 1px solid var(--linha);
}
.opcoes { display: flex; flex-wrap: wrap; gap: 6px; }
.opcoes button {
  font-family: "IBM Plex Mono", monospace; font-size: 12px; letter-spacing: 0.04em;
  padding: 7px 12px; border-radius: 999px; cursor: pointer;
  border: 1px solid var(--linha-forte); background: transparent; color: var(--ink-2);
  transition: background .15s, color .15s, border-color .15s;
}
.opcoes button:hover { border-color: var(--acento); color: var(--ink); }
.opcoes button[aria-pressed="true"] {
  background: var(--acento); border-color: var(--acento); color: #fff;
}
.barra .aviso { font-family: "IBM Plex Mono", monospace; font-size: 11.5px; color: var(--ink-3); }

/* ---------------------------------------------------------------- mapa */
.moldura-mapa {
  position: relative; border-radius: var(--raio); overflow: hidden;
  border: 1px solid var(--linha); background: var(--agua-fundo);
  box-shadow: var(--sombra);
}
.moldura-mapa::after {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(130% 100% at 50% 0%, transparent 62%, rgba(12,26,32,.05));
}
svg.mapa { display: block; width: 100%; height: auto; }
.uf { fill: #f2f7f8; stroke: #d3e0e3; stroke-width: 1; }
.afluente { fill: none; stroke: #b6d2dd; stroke-width: 1.4; stroke-linecap: round; }
.leito { fill: none; stroke: #ffffff; stroke-width: 15; stroke-linecap: round; stroke-linejoin: round; }
.trecho { fill: none; stroke: var(--neutro); stroke-width: 10; stroke-linecap: round;
  transition: stroke .45s ease, stroke-width .2s ease; }
.correnteza {
  fill: none; stroke: rgba(255,255,255,.75); stroke-width: 1.6;
  stroke-dasharray: 7 17; animation: correr 3.2s linear infinite;
}
@keyframes correr { to { stroke-dashoffset: -44; } }
.marco { fill: var(--ink-3); }
.marco-txt { font-family: "IBM Plex Mono", monospace; font-size: 11px; fill: var(--ink-3); }
.guia, .guia-nota { stroke: var(--linha-forte); stroke-width: 1; }
text.nota { font-family: "IBM Plex Mono", monospace; font-size: 11.5px; fill: var(--ink-2); }
.pino { cursor: pointer; }
.pino .halo { fill: rgba(12,26,32,.07); transition: r .2s ease, fill .2s ease; }
.pino .ponto { fill: var(--neutro); stroke: #fff; stroke-width: 2.5; transition: fill .45s ease; }
.pino .cod { font-family: Archivo, sans-serif; font-weight: 700; font-size: 13px; fill: var(--ink);
  paint-order: stroke; stroke: #fff; stroke-width: 3px; stroke-linejoin: round; }
.pino .cidade { font-family: "IBM Plex Mono", monospace; font-size: 11px; fill: var(--ink-2);
  paint-order: stroke; stroke: #fff; stroke-width: 3px; stroke-linejoin: round; }
.pino:hover .halo, .pino:focus-visible .halo, .pino.viva .halo { r: 15; fill: rgba(12,26,32,.12); }
.pino:focus-visible { outline: none; }
.pino:focus-visible .ponto { stroke: var(--acento-forte); stroke-width: 3.5; }
.pino.parada .ponto { fill: #fff; stroke-width: 3; }
.moldura-mapa.principal { border-color: var(--linha-forte); }
.apoio-mapa { display: grid; gap: 20px; grid-template-columns: minmax(0, 1fr); margin-top: 26px; }
@media (min-width: 880px) { .apoio-mapa { grid-template-columns: minmax(0, 1fr) minmax(0, 1.05fr);
  align-items: center; } }
.explica h2 { font-size: clamp(22px, 2.6vw, 30px); line-height: 1.12; }
.explica .nota { margin-top: 12px; color: var(--ink-2); font-size: 16.5px;
  font-family: Newsreader, Georgia, "Times New Roman", serif; }
.legenda-mapa {
  display: flex; flex-wrap: wrap; gap: 8px 18px; margin-top: 16px;
  font-family: "IBM Plex Mono", monospace; font-size: 12px; color: var(--ink-2);
}
.legenda-mapa i { width: 22px; height: 5px; border-radius: 3px; display: inline-block; margin-right: 6px; }
.rotulo-mapa {
  position: absolute; left: 18px; top: 16px; z-index: 2;
  font-family: "IBM Plex Mono", monospace; font-size: 11px; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--ink-3);
}

/* ------------------------------------------------------------- graficos */
svg.grafico { display: block; width: 100%; height: auto; }
.grade { stroke: var(--linha); stroke-width: 1; }
.base { stroke: var(--linha-forte); stroke-width: 1; }
.limite { stroke: var(--critico); stroke-width: 1.4; stroke-dasharray: 5 4; opacity: .75; }
text { font-family: "IBM Plex Mono", monospace; font-size: 11.5px; fill: var(--ink-3); }
text.rotulo-serie, text.tick-limite {
  paint-order: stroke; stroke: var(--superficie); stroke-width: 3.5px; stroke-linejoin: round;
}
text.tick-limite { fill: var(--ink-2); font-size: 11px; }
text.nome-estacao { font-family: Archivo, sans-serif; font-weight: 700; font-size: 13px; fill: var(--ink); }
path.linha { fill: none; stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
path.area { stroke: none; opacity: .16; }
circle.ponta { stroke: var(--superficie); stroke-width: 2; }
.legenda { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 14px;
  font-family: "IBM Plex Mono", monospace; font-size: 12px; color: var(--ink-2); }
.chip { display: inline-flex; align-items: center; gap: 7px; }
.chip i { width: 11px; height: 11px; border-radius: 3px; }

/* ------------------------------------------------------------- estacoes */
.escada { display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(272px, 1fr)); }
.estacao {
  position: relative; background: var(--cartao); border: 1px solid var(--linha);
  border-radius: var(--raio); padding: 16px 18px 14px; box-shadow: var(--sombra);
  transition: border-color .2s, transform .2s;
}
.estacao::before {
  content: ""; position: absolute; left: 0; top: 14px; bottom: 14px; width: 3px;
  border-radius: 0 3px 3px 0; background: var(--cor-estado, var(--neutro));
}
.estacao.destaque { border-color: var(--acento); transform: translateY(-2px); }
.estacao .km { font-size: 11px; color: var(--ink-3); letter-spacing: 0.08em; }
.estacao .nome { font-family: Archivo, sans-serif; font-weight: 700; font-size: 17px; margin-top: 2px; }
.estacao .local { font-size: 13.5px; color: var(--ink-2); }
.estacao .leitura {
  display: flex; align-items: baseline; justify-content: space-between; gap: 8px;
  margin-top: 12px; flex-wrap: wrap;
}
.estacao .n {
  white-space: nowrap;
  font-family: Archivo, sans-serif; font-weight: 700; font-size: 28px;
  font-variant-numeric: tabular-nums; letter-spacing: -0.02em; color: var(--cor-estado, var(--ink));
}
.estacao .n small { font-size: 13px; font-weight: 500; color: var(--ink-2); }
.estado {
  font-family: "IBM Plex Mono", monospace; font-size: 11px; letter-spacing: .06em;
  padding: 3px 9px; border-radius: 999px; white-space: nowrap;
  color: var(--cor-estado, var(--ink-2));
  border: 1px solid color-mix(in srgb, var(--cor-estado, var(--ink-3)) 45%, transparent);
  background: color-mix(in srgb, var(--cor-estado, var(--ink-3)) 12%, transparent);
}
.estacao .faixa-spark { margin-top: 8px; }
.estacao .rodape-spark { font-family: "IBM Plex Mono", monospace; font-size: 11px;
  color: var(--ink-3); display: flex; justify-content: space-between; gap: 8px; }

/* ------------------------------------------------------------- cobertura */
.cobertura { display: grid; gap: 10px; }
.linha-cobertura {
  display: grid; grid-template-columns: 200px 1fr 132px; gap: 12px; align-items: center;
  font-size: 14px;
}
.linha-cobertura .barra-idade { height: 10px; border-radius: 5px; background: var(--linha); overflow: hidden; }
.linha-cobertura .barra-idade span { display: block; height: 100%; border-radius: 5px; }
.linha-cobertura .quando { font-family: "IBM Plex Mono", monospace; font-size: 12px;
  color: var(--ink-2); text-align: right; }
@media (max-width: 620px) { .linha-cobertura { grid-template-columns: 1fr 1fr; } .linha-cobertura .barra-idade { grid-column: 1 / -1; } }

/* --------------------------------------------------------------- tabela */
.rolagem { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
thead th {
  position: sticky; top: 0; background: var(--cartao); text-align: left;
  font-size: 11px; letter-spacing: 0.06em; color: var(--ink-3); font-weight: 500;
  padding: 12px 12px 10px; border-bottom: 1px solid var(--linha-forte); white-space: nowrap;
}
tbody th, tbody td { padding: 11px 12px; border-bottom: 1px solid var(--linha); vertical-align: baseline; }
tbody th { text-align: left; font-family: Archivo, sans-serif; font-weight: 700; font-size: 14px; white-space: nowrap; }
tbody tr:hover { background: var(--acento-suave); }
td.n { font-variant-numeric: tabular-nums; white-space: nowrap; }
.pill { font-size: 11.5px; padding: 2px 8px; border-radius: 999px; border: 1px solid var(--linha-forte); color: var(--ink-2); }
.pill.viva { color: var(--bom); border-color: color-mix(in srgb, var(--bom) 45%, transparent); }
.pill.parada { color: var(--ruim); border-color: color-mix(in srgb, var(--ruim) 45%, transparent); }

/* ---------------------------------------------------------------- rodape */
footer.creditos {
  margin-top: 72px; padding-top: 26px; border-top: 1px solid var(--linha);
  color: var(--ink-2); font-size: 14.5px; display: grid; gap: 20px;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}
footer.creditos h3 { font-size: 13px; letter-spacing: .1em; text-transform: uppercase;
  color: var(--ink-3); font-family: "IBM Plex Mono", monospace; font-weight: 500; margin-bottom: 8px; }
footer.creditos a { color: var(--acento); text-decoration-thickness: 1px; text-underline-offset: 2px; }
footer.creditos code { font-family: "IBM Plex Mono", monospace; font-size: 12.5px;
  background: var(--acento-suave); padding: 1px 5px; border-radius: 4px; }

/* ------------------------------------------------------------- tooltip */
.tip {
  position: fixed; z-index: 60; pointer-events: none; display: none;
  background: var(--superficie-2); color: var(--ink);
  border: 1px solid var(--linha-forte); border-radius: 10px;
  padding: 10px 12px; font-size: 13px; box-shadow: var(--sombra); max-width: 300px;
  font-family: "IBM Plex Mono", monospace;
}
.tip .tt { font-family: Archivo, sans-serif; font-weight: 700; font-size: 13.5px; margin-bottom: 3px; }
.tip .ts { color: var(--ink-3); font-size: 11.5px; margin-bottom: 6px; }
.tip .tl { display: flex; align-items: center; gap: 7px; }
.tip .tl i { width: 9px; height: 9px; border-radius: 2px; display: inline-block; }

/* ------------------------------------------------------------- entrada */
.revela { transition: opacity .6s ease, transform .6s ease; }
.js .revela { opacity: 0; transform: translateY(14px); }
.js .revela.visivel { opacity: 1; transform: none; }
:focus-visible { outline: 2px solid var(--acento); outline-offset: 3px; border-radius: 4px; }

@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  .correnteza, .luz.acesa { animation: none; }
  .js .revela { opacity: 1; transform: none; transition: none; }
  * { transition-duration: .01ms !important; }
}
"""
