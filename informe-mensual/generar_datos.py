# -*- coding: utf-8 -*-
"""
Genera los datos ficticios de Distribuidora Papel: las mismas exportaciones
que saldrían del ERP a fin de cada mes.

  datos/facturacion.xlsx            -> todas las facturas emitidas
  datos/cobrables_AAAA-MM.xlsx      -> partidas abiertas al cierre de cada mes
  datos/objetivos.xlsx              -> objetivo de % vencido y DSO por filial

Todo es inventado. La semilla es fija: cada corrida produce los mismos datos.
"""
import os
import random
import datetime as dt
import calendar
import pandas as pd

random.seed(2026)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")

# Filial -> clientes (nombre, facturación mensual base en €, días de atraso promedio al pagar)
FILIALES = {
    "Alemania": [("Becker Druck", 420_000, 4), ("Klein Büro", 260_000, 9), ("Weber Verlag", 180_000, 2)],
    "Países Bajos": [("Van Dijk Print", 350_000, 3), ("Bakker Papier", 220_000, 6), ("De Vries Office", 150_000, 12)],
    "Bélgica": [("Peeters Office", 300_000, 8), ("Janssens Print", 200_000, 5), ("Maes Papeterie", 120_000, 4)],
    "Austria": [("Huber Druck", 280_000, 3), ("Gruber Office", 160_000, 7), ("Wagner Papier", 110_000, 2)],
}
OBJETIVOS = {  # % vencido máx., DSO máx. (días)
    "Alemania": (8.0, 67), "Países Bajos": (8.0, 67), "Bélgica": (8.0, 68), "Austria": (7.5, 66),
    "Grupo": (8.0, 67),
}
PLAZO = 60  # días de pago pactados

PRIMER_MES = dt.date(2025, 6, 1)
ULTIMO_CIERRE = dt.date(2026, 10, 31)
ESTACIONAL = {1: .85, 2: .9, 3: 1.05, 4: 1, 5: 1.05, 6: 1, 7: .9, 8: .7, 9: 1.1, 10: 1.1, 11: 1.05, 12: .9}


def fin_de_mes(d):
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])


def atraso(cliente, fecha):
    """Días de atraso de una factura. Peeters Office empeora desde el verano de 2026:
    es la historia que el informe tiene que contar sola."""
    nombre, _, base = cliente
    extra = 0
    if nombre == "Peeters Office" and fecha >= dt.date(2026, 6, 1):
        extra = 15 * (fecha.month - 5)
    return max(-5, round(random.gauss(base + extra, 3)))


def generar_facturas():
    filas, n = [], 9_000_000
    mes = PRIMER_MES
    while mes <= ULTIMO_CIERRE:
        for filial, clientes in FILIALES.items():
            for cli in clientes:
                total_mes = cli[1] * ESTACIONAL[mes.month] * random.uniform(.9, 1.1)
                k = random.randint(8, 12)  # facturas por mes
                dias_mes = calendar.monthrange(mes.year, mes.month)[1]
                for i in range(k):
                    f = mes + dt.timedelta(days=int(dias_mes * (i + random.random()) / k))
                    venc = f + dt.timedelta(days=PLAZO)
                    n += 1
                    filas.append({
                        "Filial": filial, "Cliente": cli[0], "N.º documento": n,
                        "Fecha factura": f, "Vencimiento": venc,
                        "Fecha cobro": venc + dt.timedelta(days=atraso(cli, f)),
                        "Importe €": round(total_mes / k, 2),
                    })
        mes = (mes + dt.timedelta(days=32)).replace(day=1)
    return pd.DataFrame(filas)


def main():
    os.makedirs(OUT, exist_ok=True)
    fac = generar_facturas()
    fac.drop(columns="Fecha cobro").to_excel(os.path.join(OUT, "facturacion.xlsx"), index=False)

    # Un export de partidas abiertas por cierre: lo emitido hasta ese día y todavía sin cobrar.
    cierre = fin_de_mes(PRIMER_MES)
    while cierre <= ULTIMO_CIERRE:
        abiertas = fac[(fac["Fecha factura"] <= cierre) & (fac["Fecha cobro"] > cierre)]
        abiertas.drop(columns="Fecha cobro").to_excel(
            os.path.join(OUT, f"cobrables_{cierre:%Y-%m}.xlsx"), index=False)
        cierre = fin_de_mes(cierre + dt.timedelta(days=1))

    pd.DataFrame([{"Filial": f, "% vencido objetivo": o[0], "DSO objetivo": o[1]}
                  for f, o in OBJETIVOS.items()]).to_excel(os.path.join(OUT, "objetivos.xlsx"), index=False)
    print(f"✓ {len(fac)} facturas y {len(os.listdir(OUT)) - 2} cierres en datos/")


if __name__ == "__main__":
    main()
