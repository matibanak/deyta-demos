// Arma el PowerPoint del mes a partir de metricas.json.
// Uso: node generar_informe.js [metricas.json] [salida.pptx]
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");
const fs = require("fs");
const path = require("path");

const D = JSON.parse(fs.readFileSync(process.argv[2] || "metricas.json", "utf8"));
const OUT = process.argv[3] || `salida/Informe_credito_${D.periodo}.pptx`;

// ---------- Estilo de la empresa ficticia ----------
const NAVY = "1F2A44", TEAL = "2A9D8F", RED = "C8553D", GREEN = "3A8D5B";
const GREY = "6B7280", LIGHT = "F3F4F6", LINE = "D9DDE3", WHITE = "FFFFFF", OBJ = "8A94A6";
const FONT = "Arial";
const FILIAL_COLOR = { "Alemania": NAVY, "Países Bajos": TEAL, "Bélgica": RED, "Austria": "D9952B" };

// ---------- Formato (espacio duro entre número y unidad) ----------
const nf = (v, d = 0) => v.toLocaleString("de-DE", { minimumFractionDigits: d, maximumFractionDigits: d });
const fM = v => nf(v / 1e6, 2) + " M€";
const fK = v => nf(v / 1e3) + " k€";
const fP = v => nf(v, 1) + " %";
const fD = v => nf(v, 1) + " d";
const fVar = (cur, prev) => { const d = cur - prev; return (d > 0 ? "+" : d < 0 ? "−" : "") + fK(Math.abs(d)); };
const colorVar = (cur, prev) => (cur > prev ? RED : cur < prev ? GREEN : GREY); // en vencido, subir es malo
const [anio, mesN] = D.periodo.split("-");
const cierre = `${new Date(anio, mesN, 0).getDate()}/${mesN}/${anio}`;
const generado = D.generado.split("-").reverse().join("/");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13,33 x 7,5 in
pres.title = `Informe de crédito — ${D.mes}`;
pres.company = D.empresa;

// Cabecera: etiqueta de sección arriba, y como título la conclusión de la slide.
function cabecera(s, seccion, titulo) {
  s.background = { color: WHITE };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.12, h: 7.5, fill: { color: NAVY }, line: { color: NAVY } });
  s.addText(seccion.toUpperCase(), { x: 0.55, y: 0.35, w: 7, h: 0.28, fontFace: FONT, fontSize: 10, bold: true, color: TEAL, charSpacing: 1.5, margin: 0 });
  s.addText(titulo, { x: 0.55, y: 0.65, w: 12.2, h: 0.6, fontFace: FONT, fontSize: 24, bold: true, color: NAVY, margin: 0, fit: "shrink" });
  s.addText(`${D.empresa}  ·  ${D.mes}`, { x: 8.8, y: 0.35, w: 4, h: 0.28, fontFace: FONT, fontSize: 10, color: GREY, align: "right", margin: 0 });
  s.addShape(pres.shapes.LINE, { x: 0.55, y: 6.95, w: 12.25, h: 0, line: { color: LINE, width: 0.75 } });
  s.addText(`Fuente: exportaciones del ERP al ${cierre}  ·  Generado automáticamente el ${generado}`,
    { x: 0.55, y: 7.05, w: 9, h: 0.25, fontFace: FONT, fontSize: 8, color: GREY, margin: 0 });
  s.addText(String(pres.slides.length), { x: 12.3, y: 7.05, w: 0.5, h: 0.25, fontFace: FONT, fontSize: 8, color: GREY, align: "right", margin: 0 });
}

function kpi(s, x, y, w, etiqueta, valor, detalle, ok, colorDetalle) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 1.25, fill: { color: LIGHT }, line: { color: LIGHT } });
  if (ok !== undefined) s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.07, h: 1.25, fill: { color: ok ? GREEN : RED }, line: { color: ok ? GREEN : RED } });
  s.addText(etiqueta.toUpperCase(), { x: x + 0.25, y: y + 0.15, w: w - 0.4, h: 0.25, fontFace: FONT, fontSize: 9, bold: true, color: GREY, charSpacing: 1, margin: 0 });
  s.addText(valor, { x: x + 0.25, y: y + 0.42, w: w - 0.4, h: 0.45, fontFace: FONT, fontSize: 24, bold: true, color: NAVY, margin: 0 });
  s.addText(detalle, { x: x + 0.25, y: y + 0.88, w: w - 0.4, h: 0.25, fontFace: FONT, fontSize: 9.5,
    color: colorDetalle || (ok === false ? RED : GREY), margin: 0 });
}

const ejes = { catAxisLabelFontSize: 9, valAxisLabelFontSize: 9, catAxisLabelColor: GREY, valAxisLabelColor: GREY,
  catAxisLabelFontFace: FONT, valAxisLabelFontFace: FONT, valGridLine: { color: "E5E7EB", size: 0.5 }, catGridLine: { style: "none" },
  catAxisLineShow: false, valAxisLineShow: false, legendFontSize: 9, legendFontFace: FONT, legendColor: GREY,
  titleFontSize: 11, titleColor: NAVY, titleFontFace: FONT };

const T = D.resumen.Total;
const meses = D.serie.Total.map(p => p.mes);

// ============ 1 — Portada ============
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 0.8, w: 0.7, h: 0.7, fill: { color: TEAL }, line: { color: TEAL } });
  s.addText("DP", { x: 0.8, y: 0.8, w: 0.7, h: 0.7, fontFace: FONT, fontSize: 20, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0 });
  s.addText(D.empresa, { x: 1.7, y: 0.8, w: 6, h: 0.7, fontFace: FONT, fontSize: 16, color: WHITE, valign: "middle", margin: 0 });
  s.addText("Informe de crédito", { x: 0.8, y: 2.5, w: 11, h: 1, fontFace: FONT, fontSize: 48, bold: true, color: WHITE, margin: 0 });
  s.addText(D.mes, { x: 0.8, y: 3.5, w: 11, h: 0.7, fontFace: FONT, fontSize: 28, color: "A7C4D9", margin: 0 });
  s.addShape(pres.shapes.LINE, { x: 0.8, y: 4.5, w: 1.2, h: 0, line: { color: TEAL, width: 3 } });
  // Índice
  ["Resumen del grupo", "Vencido por filial", "DSO por filial", "Clientes con vencido"].forEach((t, i) =>
    s.addText([{ text: String(i + 2).padStart(2, "0") + "   ", options: { color: TEAL, bold: true } }, { text: t, options: { color: "C9D3E0" } }],
      { x: 0.8, y: 4.8 + i * 0.38, w: 6, h: 0.32, fontFace: FONT, fontSize: 13, margin: 0 }));
  s.addText(`Generado automáticamente el ${generado} a partir de ${D.fuentes} exportaciones del ERP`,
    { x: 0.8, y: 6.75, w: 11, h: 0.3, fontFace: FONT, fontSize: 10, color: "8C9BB0", margin: 0 });
}

// ============ 2 — Resumen del grupo ============
{
  const s = pres.addSlide();
  cabecera(s, "Resumen del grupo", D.titulos.resumen);
  const w = 2.9, gap = 0.217, y = 1.55;
  kpi(s, 0.55, y, w, "Cobrable", fM(T.cobrable), `Facturación del mes: ${fM(T.facturacion)}`);
  kpi(s, 0.55 + (w + gap), y, w, "Vencido", fK(T.vencido), `${fVar(T.vencido, T.vencido_ant)} vs. ${D.mes_anterior.toLowerCase()}`,
    undefined, colorVar(T.vencido, T.vencido_ant));
  kpi(s, 0.55 + 2 * (w + gap), y, w, "% vencido", fP(T.pct_vencido), `Objetivo: máx. ${fP(T.pct_obj)}`, T.cumple_pct);
  kpi(s, 0.55 + 3 * (w + gap), y, w, "DSO", fD(T.dso), `Objetivo: máx. ${fD(T.dso_obj)}`, T.cumple_dso);

  s.addChart(pres.charts.LINE, [
    { name: "% vencido", labels: meses, values: D.serie.Total.map(p => p.pct_vencido) },
    { name: "Objetivo", labels: meses, values: meses.map(() => T.pct_obj) },
  ], { x: 0.45, y: 3.05, w: 7.7, h: 3.8, ...ejes, chartColors: [NAVY, OBJ], lineSize: 2, lineDataSymbol: "circle", lineDataSymbolSize: 5,
    showLegend: true, legendPos: "b", valAxisLabelFormatCode: "0\" %\"", valAxisMinVal: 0,
    showTitle: true, title: "% vencido del grupo — últimos 13 meses" });

  s.addShape(pres.shapes.RECTANGLE, { x: 8.4, y: 3.15, w: 4.4, h: 3.65, fill: { color: LIGHT }, line: { color: LIGHT } });
  s.addText("LO QUE CAMBIÓ ESTE MES", { x: 8.65, y: 3.3, w: 4, h: 0.3, fontFace: FONT, fontSize: 9, bold: true, color: TEAL, charSpacing: 1, margin: 0 });
  s.addText(D.notas.map(n => ({ text: n, options: { bullet: { indent: 12 }, paraSpaceAfter: 9 } })),
    { x: 8.65, y: 3.65, w: 3.95, h: 3.05, fontFace: FONT, fontSize: 11, color: NAVY, valign: "top", margin: 0, fit: "shrink" });
}

// ============ 3 — Por filial ============
{
  const s = pres.addSlide();
  cabecera(s, "Vencido por filial", D.titulos.filiales);
  const h = { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 10.5, align: "right" };
  const filas = [[
    { text: "Filial", options: { ...h, align: "left" } }, { text: "Cobrable", options: h }, { text: "Vencido", options: h },
    { text: `vs. ${D.mes_anterior.slice(0, 3).toLowerCase()}.`, options: h }, { text: "% vencido", options: h },
    { text: "Objetivo", options: h }, { text: "", options: h },
  ]];
  const fila = (nombre, r, total) => {
    const base = total ? { bold: true, fill: { color: LIGHT } } : {};
    return [
      { text: nombre, options: { ...base, bold: true } }, { text: fM(r.cobrable), options: { ...base, align: "right" } },
      { text: fK(r.vencido), options: { ...base, align: "right", bold: true } },
      { text: fVar(r.vencido, r.vencido_ant), options: { ...base, align: "right", color: colorVar(r.vencido, r.vencido_ant) } },
      { text: fP(r.pct_vencido), options: { ...base, align: "right", bold: true, color: r.cumple_pct ? GREEN : RED } },
      { text: fP(r.pct_obj), options: { ...base, align: "right", color: GREY } },
      { text: r.cumple_pct ? "✔" : "✘", options: { ...base, align: "center", bold: true, color: r.cumple_pct ? GREEN : RED } },
    ];
  };
  D.filiales.forEach(f => filas.push(fila(f, D.resumen[f])));
  filas.push(fila("Grupo", T, true));
  s.addTable(filas, { x: 0.55, y: 1.55, w: 7.4, colW: [1.6, 1.15, 1.05, 1.1, 1.1, 0.9, 0.5], fontFace: FONT, fontSize: 12, color: NAVY,
    rowH: 0.66, valign: "middle", border: { type: "solid", pt: 0.5, color: LINE } });
  s.addText("Objetivo: porcentaje máximo de vencido sobre el cobrable de cada filial. Detalle por cliente en la página 5.",
    { x: 0.55, y: 5.75, w: 7.4, h: 0.5, fontFace: FONT, fontSize: 10, italic: true, color: GREY, margin: 0 });

  s.addChart(pres.charts.BAR, [
    { name: D.mes_anterior, labels: D.filiales, values: D.filiales.map(f => Math.round(D.resumen[f].vencido_ant / 1e3)) },
    { name: D.mes.split(" ")[0], labels: D.filiales, values: D.filiales.map(f => Math.round(D.resumen[f].vencido / 1e3)) },
  ], { x: 8.25, y: 1.45, w: 4.65, h: 5.35, barDir: "col", barGapWidthPct: 60, ...ejes, chartColors: ["C3CBD7", NAVY],
    showLegend: true, legendPos: "b", showValue: true, dataLabelFontSize: 9, dataLabelColor: GREY, dataLabelFormatCode: "#,##0",
    valAxisHidden: true, valGridLine: { style: "none" }, showTitle: true, title: "Vencido por filial (k€)" });
}

// ============ 4 — DSO por filial ============
{
  const s = pres.addSlide();
  cabecera(s, "DSO por filial", D.titulos.dso);
  // Misma escala en los cuatro gráficos, para que la comparación a simple vista sea honesta.
  const todos = D.filiales.flatMap(f => [...D.serie[f].map(p => p.dso), D.resumen[f].dso_obj]);
  const min = Math.floor((Math.min(...todos) - 3) / 5) * 5, max = Math.ceil((Math.max(...todos) + 3) / 5) * 5;
  D.filiales.forEach((f, i) => {
    const r = D.resumen[f], x = 0.45 + (i % 2) * 6.25, y = 1.45 + Math.floor(i / 2) * 2.75;
    s.addChart(pres.charts.LINE, [
      { name: "DSO", labels: meses, values: D.serie[f].map(p => p.dso) },
      { name: "Objetivo", labels: meses, values: meses.map(() => r.dso_obj) },
    ], { x, y, w: 6.1, h: 2.65, ...ejes, chartColors: [FILIAL_COLOR[f], OBJ], lineSize: 2.25, lineDataSymbol: "none",
      valAxisMinVal: min, valAxisMaxVal: max, valAxisMajorUnit: 10, showLegend: false, catAxisLabelFontSize: 8,
      showTitle: true, title: `${f}   ${fD(r.dso)}  (objetivo ${fD(r.dso_obj)})  ${r.cumple_dso ? "✔" : "✘"}`,
      titleColor: r.cumple_dso ? NAVY : RED });
  });
  s.addText("Línea continua: DSO de cada mes  ·  Línea punteada: objetivo de la filial",
    { x: 6.8, y: 1.28, w: 6, h: 0.22, fontFace: FONT, fontSize: 9, color: GREY, align: "right", margin: 0 });
}

// ============ 5 — Clientes ============
{
  const s = pres.addSlide();
  cabecera(s, "Clientes con vencido", D.titulos.clientes);
  const h = { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 10.5, align: "right" };
  const filas = [[
    { text: "Cliente", options: { ...h, align: "left" } }, { text: "Filial", options: { ...h, align: "left" } },
    { text: "Cobrable", options: h }, { text: "Vencido", options: h }, { text: `vs. ${D.mes_anterior.slice(0, 3).toLowerCase()}.`, options: h },
    { text: "1-30 días", options: h }, { text: "31-60 días", options: h }, { text: "61-90 días", options: h }, { text: "+90 días", options: h },
  ]];
  const top = D.clientes.filter(c => c.vencido > 0).slice(0, 8);
  const v = x => (x ? fK(x) : "—");
  for (const c of top) {
    const alerta = c.vencido > T.vencido * 0.3;
    filas.push([
      { text: c.cliente, options: { bold: true, color: alerta ? RED : NAVY } }, { text: c.filial, options: { color: GREY } },
      { text: fK(c.cobrable), options: { align: "right" } }, { text: fK(c.vencido), options: { align: "right", bold: true } },
      { text: fVar(c.vencido, c.vencido_ant), options: { align: "right", color: colorVar(c.vencido, c.vencido_ant) } },
      ...["1-30", "31-60", "61-90", "+90"].map(t => ({ text: v(c[t]), options: {
        align: "right", color: !c[t] ? "B0B7C3" : t !== "1-30" ? RED : NAVY, bold: !!c[t] && t !== "1-30" } })),
    ]);
  }
  const resto = D.clientes.slice(top.length).reduce((a, c) => a + c.vencido, 0);
  filas.push([
    { text: `Total grupo (${D.clientes.length} clientes)`, options: { bold: true, fill: { color: LIGHT }, colspan: 2 } },
    { text: fM(T.cobrable), options: { align: "right", bold: true, fill: { color: LIGHT } } },
    { text: fK(T.vencido), options: { align: "right", bold: true, fill: { color: LIGHT } } },
    { text: fVar(T.vencido, T.vencido_ant), options: { align: "right", fill: { color: LIGHT }, color: colorVar(T.vencido, T.vencido_ant) } },
    ...["1-30", "31-60", "61-90", "+90"].map(t => ({ text: v(D.clientes.reduce((a, c) => a + c[t], 0)),
      options: { align: "right", bold: true, fill: { color: LIGHT } } })),
  ]);
  s.addTable(filas, { x: 0.55, y: 1.55, w: 12.25, colW: [2.3, 1.6, 1.35, 1.35, 1.35, 1.1, 1.1, 1.1, 1.0], fontFace: FONT, fontSize: 11.5,
    color: NAVY, rowH: 0.47, valign: "middle", border: { type: "solid", pt: 0.5, color: LINE } });
  if (resto === 0)
    s.addText(`El resto de los clientes no tiene importes vencidos al ${cierre}.`,
      { x: 0.55, y: 1.65 + 0.47 * (filas.length), w: 12, h: 0.3, fontFace: FONT, fontSize: 10, italic: true, color: GREY, margin: 0 });
}

// ---------- Retoque final: líneas de objetivo punteadas y sin marcadores ----------
async function guardar() {
  const zip = await JSZip.loadAsync(await pres.write({ outputType: "nodebuffer" }));
  for (const nombre of Object.keys(zip.files).filter(n => /^ppt\/charts\/chart\d+\.xml$/.test(n))) {
    const xml = await zip.file(nombre).async("string");
    const nuevo = xml.replace(/<c:ser>[\s\S]*?<\/c:ser>/g, ser => {
      if (!ser.includes("<c:v>Objetivo</c:v>")) return ser;
      return ser
        .replace(/<a:ln w="\d+"/, '<a:ln w="19050"')
        .replace('<a:prstDash val="solid"/>', '<a:prstDash val="dash"/>')
        .replace(/<c:marker>[\s\S]*?<\/c:marker>/, '<c:marker><c:symbol val="none"/></c:marker>');
    });
    zip.file(nombre, nuevo);
  }
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
  console.log("✓ " + OUT);
}
guardar();
