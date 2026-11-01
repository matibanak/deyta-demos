# -*- coding: utf-8 -*-
"""
Deuda entre sociedades del mismo grupo: quién le debe a quién, y cuánto queda si se netea.

Entrada: un export de partidas abiertas de proveedores por día (datos/intercompany_AAAA-MM-DD.xlsx),
donde todas las contrapartes son sociedades del grupo. Si no existen, se generan datos ficticios.

Para cada día calcula:
  - la matriz bruta deudor × acreedor;
  - el neteo bilateral: por cada par A-B, una sola deuda neta en la dirección que corresponde;
  - la posición neta de cada sociedad contra el resto del grupo (neteo multilateral).

Salida: Grupo_neto.html, con un selector para ver cada día.
"""
import os
import glob
import json
import random
import datetime as dt
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(BASE, "datos")
SOCIEDADES = {"HQ10": "Holding", "DE10": "Alemania", "NL10": "Países Bajos", "BE10": "Bélgica", "AT10": "Austria"}
CONCEPTOS = ["Servicios de gestión", "Compra de mercadería", "Cash pooling", "Licencia de marca", "Fletes compartidos"]


def generar():
    """Tres fotos semanales de la deuda intercompany, todas inventadas."""
    random.seed(8)
    os.makedirs(DATOS, exist_ok=True)
    # relaciones con su volumen base (deudor, acreedor, k€)
    base = {}
    for d in SOCIEDADES:
        for a in SOCIEDADES:
            if d != a and random.random() < 0.8:
                base[(d, a)] = random.choice([60, 90, 140, 220, 310, 420])
    base[("BE10", "HQ10")] = 780  # Bélgica acumula deuda con la holding: es la que tiene la caja corta
    base[("HQ10", "BE10")] = 150
    for k, fecha in enumerate([dt.date(2026, 10, 15), dt.date(2026, 10, 22), dt.date(2026, 10, 29)]):
        filas, n = [], 7_000_000
        for (d, a), kb in base.items():
            total = kb * 1000 * (1 + 0.12 * k if (d, a) == ("BE10", "HQ10") else random.uniform(.85, 1.15))
            partes = random.randint(2, 5)
            for _ in range(partes):
                n += 1
                filas.append({"Sociedad": d, "Nombre 1": f"Distribuidora Papel {SOCIEDADES[a]}",
                              "Nº documento": str(n), "Concepto": random.choice(CONCEPTOS),
                              "Fecha de documento": fecha - dt.timedelta(days=random.randint(5, 80)),
                              "Importe en moneda local": round(total / partes, 2)})
        pd.DataFrame(filas).to_excel(os.path.join(DATOS, f"intercompany_{fecha}.xlsx"), index=False)


def foto(path):
    df = pd.read_excel(path)
    nombre_a_cod = {f"Distribuidora Papel {v}": k for k, v in SOCIEDADES.items()}
    df["Acreedor"] = df["Nombre 1"].map(nombre_a_cod)
    sin_mapear = df[df["Acreedor"].isna()]["Nombre 1"].unique()
    if len(sin_mapear):
        print("  ! contrapartes sin mapear:", ", ".join(sin_mapear))
    df = df.dropna(subset=["Acreedor"])
    df = df[df["Sociedad"] != df["Acreedor"]]  # una sociedad contra sí misma no se netea
    bruto = df.groupby(["Sociedad", "Acreedor"])["Importe en moneda local"].sum()

    cods = list(SOCIEDADES)
    matriz = [[round(bruto.get((d, a), 0)) for a in cods] for d in cods]
    neto, vistos = [], set()
    for (d, a), v in bruto.items():
        if (a, d) in vistos:
            continue
        vistos.add((d, a))
        dif = v - bruto.get((a, d), 0)
        if round(dif):
            deu, acr = (d, a) if dif > 0 else (a, d)
            neto.append({"deudor": deu, "acreedor": acr, "importe": round(abs(dif)),
                         "bruto_ida": round(bruto.get((deu, acr), 0)), "bruto_vuelta": round(bruto.get((acr, deu), 0))})
    neto.sort(key=lambda x: -x["importe"])
    posicion = {c: round(bruto[bruto.index.get_level_values(1) == c].sum() - bruto[bruto.index.get_level_values(0) == c].sum())
                for c in cods}  # > 0: el grupo le debe; < 0: le debe al grupo
    return {"matriz": matriz, "neto": neto, "posicion": posicion,
            "bruto_total": round(bruto.sum()), "relaciones": int((bruto > 0).sum()),
            "neto_total": sum(x["importe"] for x in neto),
            "multilateral_total": sum(v for v in posicion.values() if v > 0)}


def main():
    if not glob.glob(os.path.join(DATOS, "intercompany_*.xlsx")):
        generar()
    fotos = {}
    for p in sorted(glob.glob(os.path.join(DATOS, "intercompany_*.xlsx"))):
        fecha = os.path.basename(p)[13:23]
        fotos[fecha] = foto(p)
    data = {"empresa": "Distribuidora Papel", "sociedades": SOCIEDADES, "fotos": fotos}
    html = open(os.path.join(BASE, "plantilla.html"), encoding="utf-8").read().replace(
        "/*__DATOS__*/null", json.dumps(data, ensure_ascii=False))
    open(os.path.join(BASE, "Grupo_neto.html"), "w", encoding="utf-8").write(html)
    ultima = fotos[max(fotos)]
    print(f"✓ Grupo_neto.html — {len(fotos)} fotos. Último día: bruto {ultima['bruto_total']:,.0f} € en "
          f"{ultima['relaciones']} relaciones → neto bilateral {ultima['neto_total']:,.0f} € en {len(ultima['neto'])} pagos "
          f"→ multilateral {ultima['multilateral_total']:,.0f} €")


if __name__ == "__main__":
    main()
