# -*- coding: utf-8 -*-
"""
Forecast de caja a 13 semanas: cruza lo que se espera cobrar y pagar, semana a semana.

Entradas (datos ficticios):
  - saldo inicial: los saldos del día de la demo saldos-tesoreria
  - cobros: facturas abiertas de la demo informe-mensual, en la fecha en que cada cliente
    suele pagar de verdad (vencimiento + su atraso histórico), más las ventas presupuestadas
  - pagos: ageing de proveedores, compras futuras y compromisos (nóminas, impuestos, préstamo...)

Salida: Forecast_13_semanas.html, con dos escenarios (base y "Peeters Office no paga").
"""
import os
import sys
import json
import calendar
import datetime as dt
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(BASE, "datos")
INFORME = os.path.join(BASE, "..", "informe-mensual", "datos")
SALDOS = os.path.join(BASE, "..", "saldos-tesoreria", "datos", "saldos_hoy.csv")
HOY = dt.date(2026, 11, 2)  # lunes: la semana 1 empieza hoy
SEMANAS = 13
PLAZO_COBRO = PLAZO_PAGO = 60
COMPRAS_SOBRE_VENTAS = 0.62
CLIENTE_ESCENARIO = "Peeters Office"


def semana(fecha):
    """Índice de semana (0..12); lo atrasado cae en la semana 1, lo que pasa del horizonte se descarta."""
    i = max(0, (fecha - HOY).days // 7)
    return i if i < SEMANAS else None


def movimientos():
    """Lista de (fecha, categoría, cliente_o_None, importe con signo)."""
    mov = []
    atraso = pd.read_excel(os.path.join(DATOS, "atraso_clientes.xlsx")).set_index("Cliente")["Días de atraso"]

    # Cobros de facturas ya emitidas: cuando el cliente suele pagar, no cuando vence
    abiertas = pd.read_excel(os.path.join(INFORME, "cobrables_2026-10.xlsx"))
    for _, f in abiertas.iterrows():
        cobro = pd.Timestamp(f["Vencimiento"]).date() + dt.timedelta(days=int(atraso[f["Cliente"]]))
        mov.append((max(cobro, HOY), "Cobros de facturas emitidas", f["Cliente"], f["Importe €"]))

    # Ventas presupuestadas, repartidas por cliente según su peso en la facturación reciente
    fac = pd.read_excel(os.path.join(INFORME, "facturacion.xlsx"))
    fac = fac[pd.to_datetime(fac["Fecha factura"]) >= pd.Timestamp("2026-08-01")]
    peso = fac.groupby(["Filial", "Cliente"])["Importe €"].sum() / fac.groupby("Filial")["Importe €"].sum()
    for _, v in pd.read_excel(os.path.join(DATOS, "ventas_presupuesto.xlsx")).iterrows():
        y, m = map(int, v["Mes"].split("-"))
        dias = calendar.monthrange(y, m)[1]
        for cli, w in peso[v["Filial"]].items():
            for d in range(1, dias + 1, 7):  # facturación semanal dentro del mes
                emision = dt.date(y, m, d)
                importe = v["Ventas"] * w / len(range(1, dias + 1, 7))
                mov.append((emision + dt.timedelta(days=PLAZO_COBRO + int(atraso[cli])), "Cobros de ventas nuevas", cli, importe))
                mov.append((emision + dt.timedelta(days=PLAZO_PAGO), "Proveedores", None, -importe * COMPRAS_SOBRE_VENTAS))

    for _, p in pd.read_excel(os.path.join(DATOS, "ageing_proveedores.xlsx")).iterrows():
        mov.append((max(pd.Timestamp(p["Vencimiento"]).date(), HOY), "Proveedores", None, -p["Importe"]))
    for _, c in pd.read_excel(os.path.join(DATOS, "compromisos.xlsx")).iterrows():
        mov.append((pd.Timestamp(c["Fecha"]).date(), c["Concepto"], None, -c["Importe"]))
    return mov


def escenario(mov, saldo_inicial, excluir=None):
    cats = {}
    for fecha, cat, cli, imp in mov:
        w = semana(fecha)
        if w is None or (excluir and cli == excluir):
            continue
        cats.setdefault(cat, [0.0] * SEMANAS)[w] += imp
    orden = ["Cobros de facturas emitidas", "Cobros de ventas nuevas", "Proveedores", "Nóminas", "Seguridad social",
             "Impuestos", "Préstamo", "Alquileres y servicios", "Pagos acordados"]
    filas = [{"concepto": c, "valores": [round(x) for x in cats[c]]} for c in orden if c in cats]
    neto = [sum(f["valores"][i] for f in filas) for i in range(SEMANAS)]
    saldo, s = [], saldo_inicial
    for n in neto:
        s += n
        saldo.append(round(s))
    return {"filas": filas, "neto": neto, "saldo": saldo}


def main():
    if not os.path.isdir(INFORME):
        sys.exit("Falta correr primero informe-mensual/generar_datos.py (de ahí salen las facturas abiertas).")
    if not os.path.isdir(DATOS):
        sys.path.insert(0, BASE)
        import generar_datos
        generar_datos.main()
    saldo_inicial = round(pd.read_csv(SALDOS)["Saldo"].sum()) if os.path.exists(SALDOS) else 3_760_000

    mov = movimientos()
    lunes = [HOY + dt.timedelta(days=7 * i) for i in range(SEMANAS)]
    data = {
        "empresa": "Distribuidora Papel",
        "saldo_inicial": saldo_inicial,
        "semanas": [f"S{i + 1}" for i in range(SEMANAS)],
        "desde": [d.isoformat() for d in lunes],
        "colchon": 1_000_000,  # saldo mínimo que la empresa quiere tener siempre
        "cliente_escenario": CLIENTE_ESCENARIO,
        "escenarios": {"base": escenario(mov, saldo_inicial), "sin_cliente": escenario(mov, saldo_inicial, CLIENTE_ESCENARIO)},
    }
    html = open(os.path.join(BASE, "plantilla.html"), encoding="utf-8").read().replace(
        "/*__DATOS__*/null", json.dumps(data, ensure_ascii=False))
    open(os.path.join(BASE, "Forecast_13_semanas.html"), "w", encoding="utf-8").write(html)
    for k, e in data["escenarios"].items():
        i = e["saldo"].index(min(e["saldo"]))
        print(f"✓ {k}: mínimo {min(e['saldo']):,.0f} € en S{i + 1} (semana del {lunes[i]:%d/%m}), final {e['saldo'][-1]:,.0f} €")


if __name__ == "__main__":
    main()
