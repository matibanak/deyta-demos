// Arma el PowerPoint del mes a partir de metricas.json.
// Uso: node generar_informe.js [metricas.json] [salida.pptx]
const pptxgen = require("pptxgenjs");
const fs = require("fs");

const D = JSON.parse(fs.readFileSync(process.argv[2] || "metricas.json", "utf8"));
const OUT = process.argv[3] || `salida/Informe_credito_${D.periodo}.pptx`;

// ---------- Estilo de la empresa ficticia ----------
const NAVY = "1F2A44", TEAL = "2A9D8F", RED = "C8553D", GREEN = "3A8D5B";
const GREY = "6B7280", LIGHT = "F3F4F6", LINE = "D9DDE3", WHITE = "FFFFFF";
const FONT = "Arial";
const FILIAL_COLOR = { "Alemania": NAVY, "Países Bajos": TEAL, "Bélgica": RED, "Austria": "E9A23B" };

// ---------- Formato ----------
const nf = (v, d = 0) => v.toLocaleString("de-DE", { minimumFractionDigits: d, maximumFractionDigits: d });
const fM = v => nf(v / 1e6, 2) + " M€";
const fK = v => nf(v / 1e3) + " k€";
const fP = v => nf(v, 1) + " %";
const fD = v => nf(v, 1) + " d";
const fVar = (cur, prev) => { const d = cur - prev; return (d > 0 ? "+" : d < 0 ? "−" : "") + fK(Math.abs(d)); };
const [anio, mesN] = D.periodo.split("-");
const cierre = `${new Date(anio, mesN, 0).getDate()}/${mesN}/${anio}`;
const generado = D.generado.split("-").reverse().join("/");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13,33 x 7,5 in
pres.title = `Informe de crédito — ${D.mes}`;

function cabecera(s, titulo, subtitulo) {
  s.background = { color: WHITE };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.12, h: 7.5, fill: { color: NAVY }, line: { color: NAVY } });
  s.addText(titulo, { x: 0.55, y: 0.35, w: 9, h: 0.55, fontFace: FONT, fontSize: 24, bold: true, color: NAVY, margin: 0 });
  if (subtitulo) s.addText(subtitulo, { x: 0.55, y: 0.9, w: 10, h: 0.35, fontFace: FONT, fontSize: 12, color: GREY, margin: 0 });
  s.addText(`${D.empresa}  ·  ${D.mes}`, { x: 8.8, y: 0.38, w: 4, h: 0.3, fontFace: FONT, fontSize: 10, color: GREY, align: "right", margin: 0 });
  s.addText(`Fuente: exportaciones del ERP al ${cierre}  ·  Generado automáticamente el ${generado}`,
    { x: 0.55, y: 7.05, w: 9, h: 0.25, fontFace: FONT, fontSize: 8, color: GREY, margin: 0 });
  s.addText(String(pres.slides.length), { x: 12.3, y: 7.05, w: 0.5, h: 0.25, fontFace: FONT, fontSize: 8, color: GREY, align: "right", margin: 0 });
}

function kpi(s, x, y, w, etiqueta, valor, detalle, ok) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 1.25, fill: { color: LIGHT }, line: { color: LIGHT } });
  if (ok !== undefined) s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.07, h: 1.25, fill: { color: ok ? GREEN : RED }, line: { color: ok ? GREEN : RED } });
  s.addText(etiqueta.toUpperCase(), { x: x + 0.25, y: y + 0.15, w: w - 0.4, h: 0.25, fontFace: FONT, fontSize: 9, bold: true, color: GREY, charSpacing: 1, margin: 0 });
  s.addText(valor, { x: x + 0.25, y: y + 0.42, w: w - 0.4, h: 0.45, fontFace: FONT, fontSize: 24, bold: true, color: NAVY, margin: 0 });
  s.addText(detalle, { x: x + 0.25, y: y + 0.88, w: w - 0.4, h: 0.25, fontFace: FONT, fontSize: 9.5, color: ok === false ? RED : GREY, margin: 0 });
}

const ejes = { catAxisLabelFontSize: 9, valAxisLabelFontSize: 9, catAxisLabelColor: GREY, valAxisLabelColor: GREY,
  catAxisLabelFontFace: FONT, valAxisLabelFontFace: FONT, valGridLine: { color: "E5E7EB", size: 0.5 }, catGridLine: { style: "none" },
  catAxisLineShow: false, valAxisLineShow: false, legendFontSize: 9, legendFontFace: FONT, legendColor: GREY };

const T = D.resumen.Total;
const meses = D.serie.Total.map(p => p.mes);

// ============ 1 — Portada ============
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 0.8, w: 0.7, h: 0.7, fill: { color: TEAL }, line: { color: TEAL } });
  s.addText("DP", { x: 0.8, y: 0.8, w: 0.7, h: 0.7, fontFace: FONT, fontSize: 20, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0 });
  s.addText(D.empresa, { x: 1.7, y: 0.8, w: 6, h: 0.7, fontFace: FONT, fontSize: 16, color: WHITE, valign: "middle", margin: 0 });
  s.addText("Informe de crédito", { x: 0.8, y: 2.7, w: 11, h: 1, fontFace: FONT, fontSize: 48, bold: true, color: WHITE, margin: 0 });
  s.addText(D.mes, { x: 0.8, y: 3.7, w: 11, h: 0.7, fontFace: FONT, fontSize: 28, color: "A7C4D9", margin: 0 });
  s.addShape(pres.shapes.LINE, { x: 0.8, y: 4.7, w: 1.2, h: 0, line: { color: TEAL, width: 3 } });
  s.addText(`Cobrables, vencido y DSO de las ${D.filiales.length} filiales`, { x: 0.8, y: 4.95, w: 11, h: 0.4, fontFace: FONT, fontSize: 14, color: "C9D3E0", margin: 0 });
  s.addText(`Generado automáticamente el ${generado} a partir de ${D.fuentes} exportaciones del ERP`,
    { x: 0.8, y: 6.6, w: 11, h: 0.3, fontFace: FONT, fontSize: 10, color: "8C9BB0", margin: 0 });
}

// ============ 2 — Resumen del grupo ============
{
  const s = pres.addSlide();
  cabecera(s, "Resumen del grupo", `Cierre al ${cierre}`);
  const w = 2.9, gap = 0.2;
  kpi(s, 0.55, 1.45, w, "Cobrable", fM(T.cobrable), `Facturación del mes: ${fM(T.facturacion)}`);
  kpi(s, 0.55 + (w + gap), 1.45, w, "Vencido", fK(T.vencido), `${fVar(T.vencido, T.vencido_ant)} vs. mes anterior`);
  kpi(s, 0.55 + 2 * (w + gap), 1.45, w, "% vencido", fP(T.pct_vencido), `Objetivo ${fP(T.pct_obj)}`, T.cumple_pct);
  kpi(s, 0.55 + 3 * (w + gap), 1.45, w, "DSO", fD(T.dso), `Objetivo ${fD(T.dso_obj)}`, T.cumple_dso);

  s.addChart(pres.charts.LINE, [
    { name: "% vencido", labels: meses, values: D.serie.Total.map(p => p.pct_vencido) },
    { name: "Objetivo", labels: meses, values: meses.map(() => T.pct_obj) },
  ], { x: 0.45, y: 3.0, w: 7.6, h: 3.9, ...ejes, chartColors: [NAVY, RED], lineSize: 2, lineDataSymbol: "circle", lineDataSymbolSize: 5,
    showLegend: true, legendPos: "b", valAxisLabelFormatCode: "0\"%\"", valAxisMinVal: 0,
    showTitle: true, title: "% vencido del grupo — últimos 13 meses", titleFontSize: 11, titleColor: NAVY, titleFontFace: FONT });

  s.addShape(pres.shapes.RECTANGLE, { x: 8.35, y: 3.1, w: 4.45, h: 3.75, fill: { color: LIGHT }, line: { color: LIGHT } });
  s.addText("LO QUE CAMBIÓ ESTE MES", { x: 8.6, y: 3.25, w: 4, h: 0.3, fontFace: FONT, fontSize: 9, bold: true, color: TEAL, charSpacing: 1, margin: 0 });
  s.addText(D.notas.map(n => ({ text: n, options: { bullet: { indent: 12 }, paraSpaceAfter: 8 } })),
    { x: 8.6, y: 3.6, w: 4.05, h: 3.1, fontFace: FONT, fontSize: 11, color: NAVY, valign: "top", margin: 0 });
}

// ============ 3 — Por filial ============
{
  const s = pres.addSlide();
  cabecera(s, "Vencido por filial", "Situación al cierre y comparación con el mes anterior");
  const h = { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 10 };
  const filas = [[
    { text: "Filial", options: h }, { text: "Cobrable", options: { ...h, align: "right" } },
    { text: "Vencido", options: { ...h, align: "right" } }, { text: "vs. mes ant.", options: { ...h, align: "right" } },
    { text: "% vencido", options: { ...h, align: "right" } }, { text: "Objetivo", options: { ...h, align: "right" } },
    { text: "", options: h },
  ]];
  for (const f of D.filiales) {
    const r = D.resumen[f];
    filas.push([
      { text: f, options: { bold: true } }, { text: fM(r.cobrable), options: { align: "right" } },
      { text: fK(r.vencido), options: { align: "right" } }, { text: fVar(r.vencido, r.vencido_ant), options: { align: "right", color: GREY } },
      { text: fP(r.pct_vencido), options: { align: "right", bold: true, color: r.cumple_pct ? GREEN : RED } },
      { text: fP(r.pct_obj), options: { align: "right", color: GREY } },
      { text: r.cumple_pct ? "✔" : "✘", options: { align: "center", bold: true, color: r.cumple_pct ? GREEN : RED } },
    ]);
  }
  filas.push([
    { text: "Grupo", options: { bold: true, fill: { color: LIGHT } } }, { text: fM(T.cobrable), options: { align: "right", bold: true, fill: { color: LIGHT } } },
    { text: fK(T.vencido), options: { align: "right", bold: true, fill: { color: LIGHT } } }, { text: fVar(T.vencido, T.vencido_ant), options: { align: "right", fill: { color: LIGHT } } },
    { text: fP(T.pct_vencido), options: { align: "right", bold: true, fill: { color: LIGHT } } }, { text: fP(T.pct_obj), options: { align: "right", fill: { color: LIGHT } } },
    { text: T.cumple_pct ? "✔" : "✘", options: { align: "center", bold: true, color: T.cumple_pct ? GREEN : RED, fill: { color: LIGHT } } },
  ]);
  s.addTable(filas, { x: 0.55, y: 1.5, w: 7.3, colW: [1.6, 1.15, 1.05, 1.1, 1.0, 0.9, 0.5], fontFace: FONT, fontSize: 11, color: NAVY,
    rowH: 0.62, valign: "middle", border: { type: "solid", pt: 0.5, color: LINE } });

  s.addChart(pres.charts.BAR, [
    { name: D.mes_anterior, labels: D.filiales, values: D.filiales.map(f => Math.round(D.resumen[f].vencido_ant / 1e3)) },
    { name: D.mes.split(" ")[0], labels: D.filiales, values: D.filiales.map(f => Math.round(D.resumen[f].vencido / 1e3)) },
  ], { x: 8.2, y: 1.35, w: 4.7, h: 4.6, barDir: "col", barGapWidthPct: 60, ...ejes, chartColors: ["B8C2D1", NAVY],
    showLegend: true, legendPos: "b", showValue: true, dataLabelFontSize: 8, dataLabelColor: GREY, dataLabelFormatCode: "#,##0",
    showTitle: true, title: "Vencido por filial (k€)", titleFontSize: 11, titleColor: NAVY, titleFontFace: FONT });

  const peor = D.filiales.filter(f => !D.resumen[f].cumple_pct);
  if (peor.length)
    s.addText(`${peor.join(" y ")} explica${peor.length > 1 ? "n" : ""} la mayor parte del vencido del grupo. Detalle por cliente en la página 5.`,
      { x: 0.55, y: 5.55, w: 7.3, h: 0.6, fontFace: FONT, fontSize: 11, italic: true, color: GREY, margin: 0 });
}

// ============ 4 — DSO por filial ============
{
  const s = pres.addSlide();
  cabecera(s, "DSO por filial", "Días de venta en la calle (método count-back) frente al objetivo de cada filial");
  D.filiales.forEach((f, i) => {
    const r = D.resumen[f], x = 0.45 + (i % 2) * 6.25, y = 1.35 + Math.floor(i / 2) * 2.85;
    const valores = D.serie[f].map(p => p.dso);
    const min = Math.floor((Math.min(...valores, r.dso_obj) - 4) / 5) * 5, max = Math.ceil((Math.max(...valores, r.dso_obj) + 4) / 5) * 5;
    s.addChart(pres.charts.LINE, [
      { name: "DSO", labels: meses, values: valores },
      { name: "Objetivo", labels: meses, values: meses.map(() => r.dso_obj) },
    ], { x, y, w: 6.1, h: 2.75, ...ejes, chartColors: [FILIAL_COLOR[f], "9CA3AF"], lineSize: 2, lineDataSymbol: "none",
      valAxisMinVal: min, valAxisMaxVal: max, showLegend: false, catAxisLabelFontSize: 8,
      showTitle: true, title: `${f} — ${fD(r.dso)} / objetivo ${fD(r.dso_obj)}  ${r.cumple_dso ? "✔" : "✘"}`,
      titleFontSize: 11, titleColor: r.cumple_dso ? NAVY : RED, titleFontFace: FONT });
  });
}

// ============ 5 — Clientes ============
{
  const s = pres.addSlide();
  cabecera(s, "Clientes con vencido", "Ordenados por importe vencido, con antigüedad de la deuda");
  const h = { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 10, align: "right" };
  const filas = [[
    { text: "Cliente", options: { ...h, align: "left" } }, { text: "Filial", options: { ...h, align: "left" } },
    { text: "Cobrable", options: h }, { text: "Vencido", options: h }, { text: "vs. mes ant.", options: h },
    { text: "1-30 d", options: h }, { text: "31-60 d", options: h }, { text: "61-90 d", options: h }, { text: "+90 d", options: h },
  ]];
  const top = D.clientes.filter(c => c.vencido > 0).slice(0, 8);
  const v = x => (x ? fK(x) : "—");
  for (const c of top) {
    const alerta = c.vencido > T.vencido * 0.3;
    filas.push([
      { text: c.cliente, options: { bold: true, color: alerta ? RED : NAVY } }, { text: c.filial, options: { color: GREY } },
      { text: fK(c.cobrable), options: { align: "right" } }, { text: fK(c.vencido), options: { align: "right", bold: true } },
      { text: fVar(c.vencido, c.vencido_ant), options: { align: "right", color: GREY } },
      ...["1-30", "31-60", "61-90", "+90"].map(t => ({ text: v(c[t]), options: { align: "right", color: c[t] && t !== "1-30" ? RED : NAVY } })),
    ]);
  }
  s.addTable(filas, { x: 0.55, y: 1.5, w: 12.25, colW: [2.3, 1.6, 1.35, 1.35, 1.35, 1.1, 1.1, 1.1, 1.0], fontFace: FONT, fontSize: 11,
    color: NAVY, rowH: 0.45, valign: "middle", border: { type: "solid", pt: 0.5, color: LINE } });
  const conc = top[0];
  s.addText(`${conc.cliente} representa el ${nf(conc.vencido / T.vencido * 100)} % del vencido del grupo.`,
    { x: 0.55, y: 1.6 + 0.45 * (top.length + 1), w: 12, h: 0.4, fontFace: FONT, fontSize: 11, italic: true, color: GREY, margin: 0 });
}

fs.mkdirSync(require("path").dirname(OUT), { recursive: true });
pres.writeFile({ fileName: OUT }).then(f => console.log("✓ " + f));
