# -*- coding: utf-8 -*-
"""
Lee los ficheros de la mañana y arma el dashboard de saldos: un único HTML
autocontenido (se abre con doble clic, no necesita servidor ni internet).

  datos/saldos_hoy.csv + datos/movimientos_previstos.xlsx  ->  Saldos_tesoreria.html

Para cada cuenta proyecta el saldo de los próximos 10 días hábiles sumando
los cobros y pagos previstos, y marca las cuentas que entran en negativo.
"""
import os
import json
import datetime as dt
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(BASE, "datos")
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


def main():
    if not os.path.isdir(DATOS):  # primera vez: crear los ficheros ficticios
        import generar_datos
        generar_datos.main()
    saldos = pd.read_csv(os.path.join(DATOS, "saldos_hoy.csv"))
    movs = pd.read_excel(os.path.join(DATOS, "movimientos_previstos.xlsx"))
    movs["Fecha valor"] = pd.to_datetime(movs["Fecha valor"]).dt.date

    hoy = min(movs["Fecha valor"])
    fechas = sorted(movs["Fecha valor"].unique())

    cuentas, alertas = [], []
    for _, c in saldos.iterrows():
        m = movs[movs["Cuenta"] == c["Cuenta"]]
        saldo, proy, detalle = float(c["Saldo"]), [], {}
        for f in fechas:
            del_dia = m[m["Fecha valor"] == f]
            saldo += del_dia["Importe"].sum()
            proy.append(round(saldo))
            if len(del_dia):
                detalle[f.isoformat()] = del_dia[["Tipo", "Concepto", "Importe"]].to_dict("records")
        cuentas.append({"cuenta": c["Cuenta"], "filial": c["Filial"], "banco": c["Banco"],
                        "saldo_inicial": float(c["Saldo"]), "proyeccion": proy, "detalle": detalle})
        negativo = next((i for i, v in enumerate(proy) if v < 0), None)
        if negativo is not None:
            alertas.append({"cuenta": c["Cuenta"], "filial": c["Filial"], "banco": c["Banco"],
                            "fecha": fechas[negativo].isoformat(), "minimo": min(proy),
                            "fecha_minimo": fechas[proy.index(min(proy))].isoformat()})

    data = {
        "empresa": "Distribuidora Papel",
        "generado": dt.datetime.combine(hoy, dt.time(8, 30)).isoformat(),
        "fechas": [f.isoformat() for f in fechas],
        "etiquetas": [f"{DIAS[f.weekday()]} {f:%d/%m}" for f in fechas],
        "cuentas": cuentas,
        "alertas": alertas,
    }
    plantilla = open(os.path.join(BASE, "plantilla.html"), encoding="utf-8").read()
    html = plantilla.replace("/*__DATOS__*/null", json.dumps(data, ensure_ascii=False, default=str))
    salida = os.path.join(BASE, "Saldos_tesoreria.html")
    open(salida, "w", encoding="utf-8").write(html)
    print(f"✓ Saldos_tesoreria.html — {len(cuentas)} cuentas, {len(fechas)} días, {len(alertas)} alerta(s)")
    for a in alertas:
        print(f"  ! {a['cuenta']} ({a['filial']}) entra en negativo el {a['fecha']}, mínimo {a['minimo']:,.0f} €")


if __name__ == "__main__":
    main()
