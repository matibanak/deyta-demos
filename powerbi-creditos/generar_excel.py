# -*- coding: utf-8 -*-
"""
Arma los Excel de carga de un dashboard de créditos en Power BI con datos ficticios,
con las mismas hojas y columnas que los exports estándar de SAP (FBL5N / FBL3N):

  datos/OVERDUE y DSO TEMPLATE.xlsx       -> mes actual (M)
  datos/OVERDUE y DSO TEMPLATE M-1.xlsx   -> mes anterior (M-1)

Usa las mismas facturas inventadas que la demo informe-mensual, así los números
de Distribuidora Papel coinciden en todas las demos.

Uso: python generar_excel.py [AAAA-MM]   (por defecto, el último cierre)
"""
import os
import sys
import glob
import random
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
FUENTE = os.path.join(BASE, "..", "informe-mensual", "datos")
OUT = os.path.join(BASE, "datos")
random.seed(5)

SOCIEDAD = {"Alemania": "DE10", "Países Bajos": "NL10", "Bélgica": "BE10", "Austria": "AT10"}
# Delegaciones (área de reclamación) por cliente, y su branch
DELEGACIONES = [
    (110, "Hamburgo", "GERMANY DISTRIBUTION", "GERMANY"), (120, "Múnich", "GERMANY DISTRIBUTION", "GERMANY"),
    (210, "Róterdam", "NETHERLANDS DISTRIBUTION", "NETHERLANDS"), (220, "Utrecht", "NETHERLANDS DISTRIBUTION", "NETHERLANDS"),
    (310, "Bruselas", "BELGIUM DISTRIBUTION", "BELGIUM"), (320, "Amberes", "BELGIUM DISTRIBUTION", "BELGIUM"),
    (410, "Viena", "AUSTRIA DISTRIBUTION", "AUSTRIA"),
]
CLIENTE_DELEG = {
    "Becker Druck": 110, "Klein Büro": 120, "Weber Verlag": 110,
    "Van Dijk Print": 210, "Bakker Papier": 220, "De Vries Office": 210,
    "Peeters Office": 310, "Janssens Print": 320, "Maes Papeterie": 310,
    "Huber Druck": 410, "Gruber Office": 410, "Wagner Papier": 410,
}
CUENTA = {c: str(1_000_100 + i) for i, c in enumerate(CLIENTE_DELEG)}

COLS_OD = ["Sociedad", "Ejercicio / mes", "Cuenta", "Nombre 1", "Área de reclamación", "Referencia",
           "Clase de documento", "Indicador CME", "Nº documento", "Fecha de documento", "Fe.contabilización",
           "Vencimiento neto", "Importe en ML2", "VARIABLE"]
COLS_INV = ["Sociedad", "Ejercicio / mes", "Cuenta", "Nombre 1", "Area Reclamacion", "Referencia",
            "Clase de documento", "Indicador CME", "Nº documento", "Fecha de documento", "Fe.contabilización",
            "Vencimiento neto", "Importe en ML2", "Mon.local 2", "VARIABLE"]
COLS_RAP = ["Referencia", "Nº documento", "Clase de documento", "Fecha de documento", "Fecha valor", "Clave contabiliz.",
            "Importe en moneda local", "Moneda local", "Importe en moneda doc.", "Moneda del documento", "Texto",
            "Indicador Debe/Haber", "Ejercicio / mes", "Compañía"]


def filas_sap(df, variable, area_col="Área de reclamación"):
    """Facturas del generador -> filas con el formato del export de partidas de clientes."""
    out = pd.DataFrame({
        "Sociedad": df["Filial"].map(SOCIEDAD),
        "Ejercicio / mes": pd.to_datetime(df["Fecha factura"]).dt.strftime("%Y/%m"),
        "Cuenta": df["Cliente"].map(CUENTA),
        "Nombre 1": df["Cliente"],
        area_col: df["Cliente"].map(CLIENTE_DELEG),
        "Referencia": "FV" + df["N.º documento"].astype(str).str[-6:],
        "Clase de documento": "ZF",
        "Indicador CME": "",
        "Nº documento": df["N.º documento"].astype(str),
        "Fecha de documento": pd.to_datetime(df["Fecha factura"]),
        "Fe.contabilización": pd.to_datetime(df["Fecha factura"]),
        "Vencimiento neto": pd.to_datetime(df["Vencimiento"]),
        "Importe en ML2": df["Importe €"].round(2),
    })
    if area_col == "Area Reclamacion":
        out["Mon.local 2"] = "EUR"
    out["VARIABLE"] = variable
    return out


def rappels(periodo, n=14):
    """Abonos por rappel (notas de crédito ZJ), como los que identifica el FBL3N."""
    filas = []
    for i in range(n):
        cli = random.choice(list(CLIENTE_DELEG))
        filial = next(f for f, s in SOCIEDAD.items() if CLIENTE_DELEG[cli] // 100 == list(SOCIEDAD).index(f) + 1)
        p = periodo - random.randint(0, 5)
        fecha = p.start_time + pd.Timedelta(days=random.randint(0, 25))
        imp = round(random.uniform(800, 9000), 2)
        filas.append([f"RAP{p.year}{i:03d}", str(4_900_000 + i), "ZJ", fecha, fecha, "40", imp, "EUR", imp, "EUR",
                      f"Rappel {p.year} {cli}", "S", p.strftime("%Y/%m"), SOCIEDAD[filial]])
    return pd.DataFrame(filas, columns=COLS_RAP)


def libro(periodo, fac):
    cierre = pd.Timestamp(periodo.end_time.date())
    ab_m = pd.read_excel(os.path.join(FUENTE, f"cobrables_{periodo}.xlsx"))
    ab_m1 = pd.read_excel(os.path.join(FUENTE, f"cobrables_{periodo - 1}.xlsx"))
    vencidas = ab_m[pd.to_datetime(ab_m["Vencimiento"]) < cierre]

    od = pd.concat([filas_sap(vencidas, "OVERDUE"), filas_sap(ab_m, "RECEIVABLE M")], ignore_index=True)
    f5 = fac[pd.to_datetime(fac["Fecha factura"]).dt.to_period("M").between(periodo - 4, periodo)]
    inv = pd.concat([filas_sap(ab_m, "RECEIVABLE M", "Area Reclamacion"),
                     filas_sap(ab_m1, "RECEIVABLE M-1", "Area Reclamacion"),
                     filas_sap(f5, "INVOICING", "Area Reclamacion")], ignore_index=True)
    deleg = pd.DataFrame(DELEGACIONES, columns=["Codigo Delegacion", "Delegacion", "Descripción Branch", "Country"])

    nombre = "OVERDUE y DSO TEMPLATE.xlsx" if periodo == PERIODO else "OVERDUE y DSO TEMPLATE M-1.xlsx"
    with pd.ExcelWriter(os.path.join(OUT, nombre), engine="openpyxl", datetime_format="DD/MM/YYYY") as xw:
        od.to_excel(xw, "CONSOLIDADO OVERDUE+RCV", index=False)
        inv.to_excel(xw, "CONSOLIDADO INV+RCV", index=False)
        rappels(periodo).to_excel(xw, "FBL3N LAYOUT RAPPELS", index=False)
        deleg.to_excel(xw, "DELEGACIONES-BRANCH", index=False)
        deleg.to_excel(xw, "Delegaciones hasta 2023", index=False)
        pd.DataFrame({"Datos ficticios": ["Generado por generar_excel.py (deyta-demos)."]}).to_excel(
            xw, "PISTAS & INSTRUCCIONES", index=False)
    print(f"✓ datos/{nombre}: {len(od)} filas overdue+rcv, {len(inv)} filas inv+rcv")


if __name__ == "__main__":
    if not os.path.isdir(FUENTE):
        sys.exit("Falta correr primero informe-mensual/generar_datos.py")
    cierres = sorted(os.path.basename(f)[10:17] for f in glob.glob(os.path.join(FUENTE, "cobrables_*.xlsx")))
    PERIODO = pd.Period(sys.argv[1] if len(sys.argv) > 1 else cierres[-1], "M")
    os.makedirs(OUT, exist_ok=True)
    fac = pd.read_excel(os.path.join(FUENTE, "facturacion.xlsx"))
    libro(PERIODO, fac)
    libro(PERIODO - 1, fac)
