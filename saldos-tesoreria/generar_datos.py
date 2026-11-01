# -*- coding: utf-8 -*-
"""
Genera los ficheros ficticios que tesorería recibe cada mañana:

  datos/saldos_hoy.csv              -> saldo de cierre de ayer por cuenta bancaria
  datos/movimientos_previstos.xlsx  -> cobros y pagos esperados, con fecha valor banco

Todo es inventado. La semilla es fija: cada corrida produce los mismos datos.
"""
import os
import random
import datetime as dt
import pandas as pd

random.seed(11)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
HOY = dt.date(2026, 11, 2)  # lunes

# filial -> cuentas (banco, saldo de hoy en €)
CUENTAS = {
    "Alemania": [("Rhein Bank", 1_240_000), ("Delta Bank", 310_000)],
    "Países Bajos": [("Delta Bank", 860_000), ("Atlas Bank", 145_000)],
    "Bélgica": [("Atlas Bank", 420_000), ("Delta Bank", 95_000)],
    "Austria": [("Alpen Bank", 690_000)],
}
CODIGO = {"Alemania": "DE", "Países Bajos": "NL", "Bélgica": "BE", "Austria": "AT"}
CLIENTES = {
    "Alemania": ["Becker Druck", "Klein Büro", "Weber Verlag"],
    "Países Bajos": ["Van Dijk Print", "Bakker Papier", "De Vries Office"],
    "Bélgica": ["Peeters Office", "Janssens Print", "Maes Papeterie"],
    "Austria": ["Huber Druck", "Gruber Office", "Wagner Papier"],
}


def dias_habiles(desde, n):
    d, out = desde, []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    dias = dias_habiles(HOY, 10)
    saldos, movs = [], []
    for filial, cuentas in CUENTAS.items():
        for i, (banco, saldo) in enumerate(cuentas):
            cuenta = f"{CODIGO[filial]}-{banco.split()[0][:3].upper()}-{i + 1:02d}"
            saldos.append({"Cuenta": cuenta, "Filial": filial, "Banco": banco, "Divisa": "EUR", "Saldo": saldo})
            principal = i == 0
            for d in dias:
                if principal:
                    # cobros de clientes casi todos los días
                    for _ in range(random.randint(1, 2)):
                        cli = random.choice(CLIENTES[filial])
                        if cli == "Peeters Office":
                            continue  # no paga: es la historia de la demo
                        movs.append((cuenta, d, "Cobro de cliente", cli, round(random.uniform(40, 160)) * 1000))
                    if random.random() < 0.45:
                        movs.append((cuenta, d, "Pago a proveedores", "Remesa de proveedores", -round(random.uniform(60, 220)) * 1000))
            if principal:
                quincena = dias[8]  # nóminas y seguros sociales
                movs.append((cuenta, quincena, "Nóminas", "Nóminas de noviembre", -round(saldo * 0.28, -3)))
                movs.append((cuenta, dias[4], "Impuestos", "IVA del trimestre", -round(saldo * 0.18, -3)))
            elif random.random() < 0.6:
                movs.append((cuenta, random.choice(dias[2:]), "Comisiones", "Comisiones bancarias", -round(random.uniform(1, 4)) * 1000))
                movs.append((cuenta, random.choice(dias[1:]), "Cobro de cliente", random.choice(CLIENTES[filial][1:]), round(random.uniform(20, 60)) * 1000))

    # La historia: Peeters Office no paga (ver arriba) y Bélgica no llega a cubrir sus pagos: la cuenta entra en negativo.
    movs.append(("BE-ATL-01", dias[5], "Pago a proveedores", "Compra de bobinas a la papelera", -110_000))

    pd.DataFrame(saldos).to_csv(os.path.join(OUT, "saldos_hoy.csv"), index=False, encoding="utf-8")
    pd.DataFrame(movs, columns=["Cuenta", "Fecha valor", "Tipo", "Concepto", "Importe"]).to_excel(
        os.path.join(OUT, "movimientos_previstos.xlsx"), index=False)
    print(f"✓ {len(saldos)} cuentas y {len(movs)} movimientos previstos en datos/")


if __name__ == "__main__":
    main()
