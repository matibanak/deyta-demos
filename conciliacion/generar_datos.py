# -*- coding: utf-8 -*-
"""
Genera un export ficticio de partidas abiertas de una cuenta puente de cobros:
del lado del banco entran los cobros (haber) y del lado de clientes se aplican
(debe). Lo normal es que casi todo se compense; algunas partidas no.

  datos/partidas_abiertas.xlsx

Todo es inventado. La semilla es fija.
"""
import os
import random
import datetime as dt
import pandas as pd

random.seed(21)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
SOCIEDADES = {"DE10": "Alemania", "NL10": "Países Bajos", "BE10": "Bélgica", "AT10": "Austria"}
CLIENTES = ["Becker Druck", "Klein Büro", "Weber Verlag", "Van Dijk Print", "Bakker Papier", "De Vries Office",
            "Peeters Office", "Janssens Print", "Maes Papeterie", "Huber Druck", "Gruber Office", "Wagner Papier"]
CUENTA = "5720001"  # cuenta puente: cobros pendientes de aplicar
INICIO = dt.date(2026, 10, 1)

filas, n = [], 4_100_000


def fecha():
    d = INICIO + dt.timedelta(days=random.randint(0, 29))
    while d.weekday() >= 5:
        d += dt.timedelta(days=1)
    return d


def mas_dias(d, k):
    while k > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            k -= 1
    return d


def partida(soc, f, imp, texto, clase):
    global n
    n += 1
    filas.append({"Sociedad": soc, "Cuenta de mayor": CUENTA, "Nº documento": str(n), "Clase de documento": clase,
                  "Fecha de documento": f, "Importe en moneda local": round(imp, 2), "Moneda local": "EUR",
                  "Texto": texto})


def importe():
    return round(random.uniform(800, 60000), 2)


for soc in SOCIEDADES:
    # 1:1 — un cobro del banco y su aplicación al cliente
    for _ in range(34):
        f, imp, cli = fecha(), importe(), random.choice(CLIENTES)
        partida(soc, f, -imp, f"Transferencia recibida {cli}", "ZB")
        partida(soc, mas_dias(f, random.randint(0, 2)), imp, f"Aplicación cobro {cli}", "DZ")
    # 1:N — un cobro que paga varias facturas
    for _ in range(5):
        f, cli = fecha(), random.choice(CLIENTES)
        partes = [importe() for _ in range(random.randint(2, 4))]
        partida(soc, f, -sum(partes), f"Transferencia recibida {cli} (varias facturas)", "ZB")
        for p in partes:
            partida(soc, mas_dias(f, random.randint(0, 2)), p, f"Aplicación cobro {cli}", "DZ")
    # N:1 — varios cobros parciales para una misma aplicación
    for _ in range(3):
        f, cli = fecha(), random.choice(CLIENTES)
        partes = [importe() for _ in range(2)]
        for p in partes:
            partida(soc, f, -p, f"Transferencia parcial {cli}", "ZB")
        partida(soc, mas_dias(f, 1), sum(partes), f"Aplicación cobro {cli}", "DZ")
    # Lo que no se compensa solo, cada caso con su motivo real
    for _ in range(3):  # cobros sin identificar
        partida(soc, fecha(), -importe(), "Transferencia recibida sin referencia", "ZB")
    f, imp = fecha(), importe()  # diferencia de un céntimo (comisión o redondeo)
    partida(soc, f, -imp, "Transferencia recibida Klein Büro", "ZB")
    partida(soc, f, imp - 0.01, "Aplicación cobro Klein Büro", "DZ")
    f, imp = dt.date(2026, 10, 2), importe()  # misma cifra, pero aplicada tres semanas después
    partida(soc, f, -imp, "Transferencia recibida Maes Papeterie", "ZB")
    partida(soc, mas_dias(f, 15), imp, "Aplicación cobro Maes Papeterie", "DZ")

random.shuffle(filas)
os.makedirs(OUT, exist_ok=True)
pd.DataFrame(filas).to_excel(os.path.join(OUT, "partidas_abiertas.xlsx"), index=False)
print(f"✓ {len(filas)} partidas abiertas en datos/partidas_abiertas.xlsx")
