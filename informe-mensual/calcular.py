# -*- coding: utf-8 -*-
"""
Lee las exportaciones de datos/ y calcula todo lo que lleva el informe del mes:
cobrable, vencido, % vencido y DSO por filial (13 meses), detalle de clientes
y las notas del mes, escritas a partir de los números.

Uso: python calcular.py [AAAA-MM]     (por defecto, el último cierre disponible)
Salida: metricas.json
"""
import os
import sys
import glob
import json
import calendar
import datetime as dt
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(BASE, "datos")
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
SERIE = 13  # meses que muestran los gráficos


def etiqueta(p):
    return f"{MESES[p.month - 1]} {p.year % 100}"


def dso(cobrable, fact_por_mes, periodo):
    """DSO por count-back: cuántos días de facturación reciente hacen falta para cubrir el cobrable."""
    resto, dias = cobrable, 0.0
    p = periodo
    for _ in range(12):
        f = fact_por_mes.get(p, 0)
        dm = calendar.monthrange(p.year, p.month)[1]
        if f <= 0:
            break
        if resto <= f:
            return round(dias + resto / f * dm, 1)
        dias += dm
        resto -= f
        p -= 1
    return round(dias, 1)


def k(v):
    """Importe en miles con separador español: 231952 -> '232 k€'."""
    return f"{v / 1e3:,.0f} k€".replace(",", ".")


def pct(v):
    return f"{v:.1f} %".replace(".", ",")


def dias(v):
    return f"{v:.1f} días".replace(".", ",")


def tramo(dias):
    if dias <= 0:
        return "No vencido"
    if dias <= 30:
        return "1-30"
    if dias <= 60:
        return "31-60"
    if dias <= 90:
        return "61-90"
    return "+90"


def main():
    cierres = sorted(os.path.basename(f)[10:17] for f in glob.glob(os.path.join(DATOS, "cobrables_*.xlsx")))
    mes = sys.argv[1] if len(sys.argv) > 1 else cierres[-1]
    M = pd.Period(mes, "M")
    periodos = [p for p in pd.period_range(M - SERIE + 1, M, freq="M") if f"{p}" in cierres]

    fac = pd.read_excel(os.path.join(DATOS, "facturacion.xlsx"))
    fac["Periodo"] = pd.to_datetime(fac["Fecha factura"]).dt.to_period("M")
    obj = pd.read_excel(os.path.join(DATOS, "objetivos.xlsx")).set_index("Filial")
    filiales = list(obj.index)

    # ---- Serie mensual por filial y total ----
    serie = {f: [] for f in filiales + ["Total"]}
    abiertas = {}
    for p in periodos:
        ab = pd.read_excel(os.path.join(DATOS, f"cobrables_{p}.xlsx"))
        cierre = pd.Timestamp(p.end_time.date())
        ab["Días vencido"] = (cierre - pd.to_datetime(ab["Vencimiento"])).dt.days
        ab["Vencido €"] = ab["Importe €"].where(ab["Días vencido"] > 0, 0)
        abiertas[p] = ab
        for f in filiales + ["Total"]:
            a = ab if f == "Total" else ab[ab["Filial"] == f]
            fx = fac if f == "Total" else fac[fac["Filial"] == f]
            fpm = fx.groupby("Periodo")["Importe €"].sum().to_dict()
            cob, ven = a["Importe €"].sum(), a["Vencido €"].sum()
            serie[f].append({
                "mes": etiqueta(p), "cobrable": round(cob), "vencido": round(ven),
                "pct_vencido": round(ven / cob * 100, 2) if cob else 0,
                "dso": dso(cob, fpm, p), "facturacion": round(fpm.get(p, 0)),
            })

    def objetivo(f, col):
        if f == "Total":  # objetivo del grupo = promedio ponderado por cobrable
            pesos = {x: serie[x][-1]["cobrable"] for x in filiales}
            return round(sum(obj.loc[x, col] * w for x, w in pesos.items()) / sum(pesos.values()), 1)
        return float(obj.loc[f, col])

    resumen = {}
    for f in filiales + ["Total"]:
        act, ant = serie[f][-1], serie[f][-2]
        resumen[f] = {**act, "pct_obj": objetivo(f, "% vencido objetivo"), "dso_obj": objetivo(f, "DSO objetivo"),
                      "vencido_ant": ant["vencido"], "pct_ant": ant["pct_vencido"], "dso_ant": ant["dso"]}
        resumen[f]["cumple_pct"] = bool(act["pct_vencido"] <= resumen[f]["pct_obj"])
        resumen[f]["cumple_dso"] = bool(act["dso"] <= resumen[f]["dso_obj"])

    # ---- Clientes del mes ----
    ab, ab_ant = abiertas[M], abiertas[periodos[-2]]
    ab["Tramo"] = ab["Días vencido"].map(tramo)
    venc_ant = ab_ant.groupby("Cliente")["Vencido €"].sum()
    clientes = []
    for (fil, cli), g in ab.groupby(["Filial", "Cliente"]):
        t = g.groupby("Tramo")["Importe €"].sum()
        clientes.append({
            "filial": fil, "cliente": cli, "cobrable": round(g["Importe €"].sum()),
            "vencido": round(g["Vencido €"].sum()), "vencido_ant": round(venc_ant.get(cli, 0)),
            **{k: round(t.get(k, 0)) for k in ["1-30", "31-60", "61-90", "+90"]},
        })
    clientes.sort(key=lambda c: -c["vencido"])

    # ---- Notas del mes: el texto sale de los números ----
    notas = []
    tot = resumen["Total"]
    dif = tot["vencido"] - tot["vencido_ant"]
    notas.append(f"El vencido del grupo {'sube' if dif > 0 else 'baja'} {k(abs(dif))} frente a "
                 f"{MESES_LARGOS[(M - 1).month - 1]} y cierra en {pct(tot['pct_vencido'])} del cobrable "
                 f"(objetivo {pct(tot['pct_obj'])}).")
    fuera = [f for f in filiales if not resumen[f]["cumple_pct"]]
    for f in fuera:
        peor = next(c for c in clientes if c["filial"] == f)
        notas.append(f"{f} queda fuera de objetivo ({pct(resumen[f]['pct_vencido'])} vs. {pct(resumen[f]['pct_obj'])}): "
                     f"{peor['cliente']} concentra {k(peor['vencido'])} vencidos.")
    if not tot["cumple_dso"]:
        peor_dso = max(filiales, key=lambda f: resumen[f]["dso"] - resumen[f]["dso_obj"])
        notas.append(f"El DSO del grupo queda en {dias(tot['dso'])}, por encima del objetivo ({dias(tot['dso_obj'])}), "
                     f"empujado por {peor_dso} ({dias(resumen[peor_dso]['dso'])}).")
    ok = [f for f in filiales if resumen[f]["cumple_pct"] and resumen[f]["cumple_dso"]]
    if ok:
        notas.append(f"{', '.join(ok[:-1]) + ' y ' + ok[-1] if len(ok) > 1 else ok[0]} "
                     f"cumple{'n' if len(ok) > 1 else ''} ambos objetivos (vencido y DSO).")
    sube = max(clientes, key=lambda c: c["vencido"] - c["vencido_ant"])
    if sube["vencido"] - sube["vencido_ant"] > 0:
        notas.append(f"Mayor aumento del mes: {sube['cliente']} ({sube['filial']}), "
                     f"+{k(sube['vencido'] - sube['vencido_ant'])} de vencido.")

    out = {
        "empresa": "Distribuidora Papel",
        "periodo": str(M), "mes": f"{MESES_LARGOS[M.month - 1].capitalize()} {M.year}",
        "mes_anterior": MESES_LARGOS[(M - 1).month - 1].capitalize(),
        "generado": dt.date.today().isoformat(),
        "fuentes": len(periodos) + 2,
        "filiales": filiales, "serie": serie, "resumen": resumen,
        "clientes": clientes, "notas": notas,
    }
    with open(os.path.join(BASE, "metricas.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f"✓ metricas.json — {out['mes']}: vencido {tot['vencido'] / 1e3:,.0f} k€ "
          f"({tot['pct_vencido']:.1f} %), DSO {tot['dso']} días")
    for n in notas:
        print("  ·", n)


if __name__ == "__main__":
    main()
