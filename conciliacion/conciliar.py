# -*- coding: utf-8 -*-
"""
Concilia las partidas abiertas de una cuenta: busca grupos que se compensan solos
y explica por qué no se compensa el resto.

Regla: un grupo se compensa si sus partidas son de la misma sociedad y cuenta,
suman exactamente 0 (al céntimo) y están a no más de TOL días hábiles de la
partida principal (la de mayor importe). Se busca primero 1:1, después 1:N y N:1,
y siempre se prefiere el grupo más chico.

  datos/partidas_abiertas.xlsx  ->  salida/conciliacion.xlsx  +  salida/informe.html

Uso: python conciliar.py [--tol 2] [--max-grupo 5]
"""
import os
import sys
import json
import argparse
import datetime as dt
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))


def habiles(a, b):
    """Días hábiles entre dos fechas, en valor absoluto."""
    a, b = sorted([np.datetime64(a, "D"), np.datetime64(b, "D")])
    return int(np.busday_count(a, b))


def buscar_subconjunto(objetivo, candidatos, max_n, presupuesto=50_000):
    """Subconjunto de candidatos [(idx, centimos)] que suma exactamente `objetivo`, el más chico primero."""
    cand = sorted(candidatos, key=lambda c: -abs(c[1]))
    nodos = 0
    for tam in range(2, max_n + 1):
        pila = [(0, 0, [])]
        while pila:
            ini, acum, elegidos = pila.pop()
            nodos += 1
            if nodos > presupuesto:
                return None
            if len(elegidos) == tam:
                if acum == objetivo:
                    return elegidos
                continue
            for j in range(len(cand) - 1, ini - 1, -1):
                pila.append((j + 1, acum + cand[j][1], elegidos + [cand[j][0]]))
    return None


def conciliar(df, tol, max_grupo):
    df = df.copy()
    df["cent"] = (df["Importe en moneda local"] * 100).round().astype(int)
    df["fecha"] = pd.to_datetime(df["Fecha de documento"]).dt.date
    df["Grupo"], df["Tipo"] = None, None
    grupo = 0

    for _, bloque in df.groupby(["Sociedad", "Cuenta de mayor"]):
        libres = set(bloque.index)

        # 1:1
        for i in sorted(bloque.index, key=lambda x: df.at[x, "fecha"]):
            if i not in libres:
                continue
            pares = [j for j in libres if j != i and df.at[j, "cent"] == -df.at[i, "cent"]
                     and habiles(df.at[i, "fecha"], df.at[j, "fecha"]) <= tol]
            if pares:
                j = min(pares, key=lambda x: habiles(df.at[i, "fecha"], df.at[x, "fecha"]))
                grupo += 1
                df.loc[[i, j], ["Grupo", "Tipo"]] = [grupo, "1:1"]
                libres -= {i, j}

        # 1:N y N:1: la partida más grande busca entre las de signo contrario
        for ancla in sorted(libres, key=lambda x: -abs(df.at[x, "cent"])):
            if ancla not in libres:
                continue
            a = df.loc[ancla]
            cand = [(j, int(df.at[j, "cent"])) for j in libres
                    if j != ancla and np.sign(df.at[j, "cent"]) == -np.sign(a["cent"])
                    and abs(df.at[j, "cent"]) < abs(a["cent"]) and habiles(a["fecha"], df.at[j, "fecha"]) <= tol]
            cand = sorted(cand, key=lambda c: habiles(a["fecha"], df.at[c[0], "fecha"]))[:30]
            hallado = buscar_subconjunto(-int(a["cent"]), cand, max_grupo - 1)
            if hallado:
                grupo += 1
                tipo = f"1:{len(hallado)}" if a["cent"] < 0 else f"{len(hallado)}:1"
                df.loc[[ancla, *hallado], ["Grupo", "Tipo"]] = [grupo, tipo]
                libres -= {ancla, *hallado}

        # Pendientes: por qué no se compensaron
        for i in libres:
            p = df.loc[i]
            otros = df.loc[list(libres - {i})]
            otros = otros[np.sign(otros["cent"]) == -np.sign(p["cent"])]
            exacto = otros[otros["cent"] == -p["cent"]]
            cerca = otros[(otros["cent"] + p["cent"]).abs().between(1, 100)]
            if len(exacto):
                o = exacto.iloc[0]
                motivo = f"Mismo importe que el doc. {o['Nº documento']}, pero a {habiles(p['fecha'], o['fecha'])} días hábiles"
            elif len(cerca):
                o = cerca.iloc[0]
                dif = (o["cent"] + p["cent"]) / 100
                motivo = f"Diferencia de {abs(dif):.2f} € con el doc. {o['Nº documento']}".replace(".", ",")
            else:
                motivo = "Sin contrapartida: cobro sin identificar" if p["cent"] < 0 else "Sin contrapartida"
            df.at[i, "Motivo"] = motivo
    return df.drop(columns=["cent", "fecha"])


def informe(df, tol, max_grupo):
    conc = df[df["Grupo"].notna()]
    pend = df[df["Grupo"].isna()].sort_values(["Sociedad", "Motivo"])
    tipos = conc.drop_duplicates("Grupo")["Tipo"].map(lambda t: "1:1" if t == "1:1" else ("1:N" if t.startswith("1:") else "N:1"))
    data = {
        "total": len(df), "conciliadas": len(conc), "pendientes": len(pend),
        "importe_pend": round(pend["Importe en moneda local"].abs().sum(), 2),
        "grupos": tipos.value_counts().reindex(["1:1", "1:N", "N:1"], fill_value=0).to_dict(),
        "tol": tol, "max_grupo": max_grupo,
        "por_sociedad": [{"soc": s, "total": int(len(g)), "pend": int(g["Grupo"].isna().sum())}
                         for s, g in df.groupby("Sociedad")],
        "pend": pend[["Sociedad", "Nº documento", "Fecha de documento", "Importe en moneda local", "Texto", "Motivo"]]
        .assign(**{"Fecha de documento": lambda x: pd.to_datetime(x["Fecha de documento"]).dt.strftime("%d/%m")})
        .to_dict("records"),
        # un grupo 1:N completo (el primero de 3 facturas, para que entre en la tarjeta)
        "ejemplo": conc[conc["Grupo"] == conc.loc[conc["Tipo"] == "1:3", "Grupo"].min()]
        .sort_values("Importe en moneda local")[["Nº documento", "Fecha de documento", "Importe en moneda local", "Texto"]]
        .assign(**{"Fecha de documento": lambda x: pd.to_datetime(x["Fecha de documento"]).dt.strftime("%d/%m")})
        .to_dict("records"),
        "generado": dt.date.today().strftime("%d/%m/%Y"),
    }
    plantilla = open(os.path.join(BASE, "plantilla.html"), encoding="utf-8").read()
    return plantilla.replace("/*__DATOS__*/null", json.dumps(data, ensure_ascii=False, default=str))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tol", type=int, default=2, help="días hábiles de tolerancia (por defecto 2)")
    ap.add_argument("--max-grupo", type=int, default=5, help="partidas máximas por grupo (por defecto 5)")
    args = ap.parse_args()

    entrada = os.path.join(BASE, "datos", "partidas_abiertas.xlsx")
    if not os.path.exists(entrada):
        sys.path.insert(0, BASE)
        import generar_datos  # noqa: F401  (genera los datos ficticios al importarse)
    df = conciliar(pd.read_excel(entrada, dtype={"Nº documento": str, "Cuenta de mayor": str}), args.tol, args.max_grupo)

    os.makedirs(os.path.join(BASE, "salida"), exist_ok=True)
    with pd.ExcelWriter(os.path.join(BASE, "salida", "conciliacion.xlsx"), engine="openpyxl") as xw:
        df[df["Grupo"].notna()].sort_values(["Grupo", "Importe en moneda local"]).drop(columns="Motivo") \
            .to_excel(xw, "Conciliadas", index=False)
        df[df["Grupo"].isna()].drop(columns=["Grupo", "Tipo"]).to_excel(xw, "Pendientes", index=False)
    open(os.path.join(BASE, "salida", "informe.html"), "w", encoding="utf-8").write(informe(df, args.tol, args.max_grupo))

    n_c = df["Grupo"].notna().sum()
    print(f"✓ {n_c} de {len(df)} partidas conciliadas ({n_c / len(df):.0%}) en {df['Grupo'].nunique()} grupos; "
          f"{len(df) - n_c} pendientes con su motivo → salida/")


if __name__ == "__main__":
    main()
