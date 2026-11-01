# -*- coding: utf-8 -*-
"""
Genera los ficheros ficticios que alimentan el forecast de caja:

  datos/ageing_proveedores.xlsx   -> facturas de proveedores pendientes de pago
  datos/compromisos.xlsx          -> nóminas, impuestos, cuotas de préstamo, pagos acordados
  datos/atraso_clientes.xlsx      -> días de atraso promedio con que paga cada cliente
  datos/ventas_presupuesto.xlsx   -> facturación esperada por filial y mes (lo que todavía no se facturó)

Los cobros de clientes salen de las facturas abiertas de la demo informe-mensual.
Todo es inventado. La semilla es fija.
"""
import os
import random
import datetime as dt
import pandas as pd

random.seed(13)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
HOY = dt.date(2026, 11, 2)
FILIALES = ["Alemania", "Países Bajos", "Bélgica", "Austria"]
PESO = {"Alemania": .3, "Países Bajos": .27, "Bélgica": .24, "Austria": .19}
PROVEEDORES = ["Papelera del Norte", "Celulosa Atlántica", "Transportes Rin", "Embalajes Centro", "Energía Alpina"]
ATRASO = {  # días promedio de atraso al pagar (histórico de los últimos 6 meses)
    "Becker Druck": 4, "Klein Büro": 9, "Weber Verlag": 2, "Van Dijk Print": 3, "Bakker Papier": 6,
    "De Vries Office": 12, "Peeters Office": 55, "Janssens Print": 5, "Maes Papeterie": 4,
    "Huber Druck": 3, "Gruber Office": 7, "Wagner Papier": 2,
}


def main():
    os.makedirs(OUT, exist_ok=True)

    # Proveedores: compras de los últimos dos meses, a 60 días
    filas = []
    for _ in range(95):
        fil, prov = random.choice(FILIALES), random.choice(PROVEEDORES)
        f = HOY - dt.timedelta(days=random.randint(1, 58))
        filas.append({"Filial": fil, "Proveedor": prov, "Fecha factura": f,
                      "Vencimiento": f + dt.timedelta(days=60), "Importe": round(random.uniform(15, 75)) * 1000})
    pd.DataFrame(filas).to_excel(os.path.join(OUT, "ageing_proveedores.xlsx"), index=False)

    # Compromisos fijos
    comp = []
    for mes in [(2026, 11), (2026, 12), (2027, 1)]:
        y, m = mes
        comp.append(("Nóminas", f"Nóminas {m:02d}/{y}", dt.date(y, m, 27), 640_000))
        comp.append(("Seguridad social", f"Cargas sociales {m:02d}/{y}", dt.date(y, m, 30) if m != 2 else dt.date(y, m, 28), 190_000))
        comp.append(("Préstamo", f"Cuota préstamo {m:02d}/{y}", dt.date(y, m, 15), 125_000))
        comp.append(("Alquileres y servicios", f"Alquileres {m:02d}/{y}", dt.date(y, m, 5), 85_000))
    comp.append(("Nóminas", "Pagas extra de diciembre", dt.date(2026, 12, 18), 610_000))
    comp.append(("Impuestos", "IVA 4.º trimestre", dt.date(2027, 1, 20), 520_000))
    comp.append(("Impuestos", "Pago a cuenta impuesto de sociedades", dt.date(2026, 12, 20), 280_000))
    comp.append(("Pagos acordados", "Inversión en almacén (2.º pago)", dt.date(2026, 12, 10), 350_000))
    pd.DataFrame(comp, columns=["Concepto", "Detalle", "Fecha", "Importe"]).to_excel(
        os.path.join(OUT, "compromisos.xlsx"), index=False)

    pd.DataFrame(list(ATRASO.items()), columns=["Cliente", "Días de atraso"]).to_excel(
        os.path.join(OUT, "atraso_clientes.xlsx"), index=False)

    ventas = [{"Filial": f, "Mes": m, "Ventas": round(3_050_000 * PESO[f] * k, -3)}
              for m, k in [("2026-11", 1.05), ("2026-12", .9), ("2027-01", .85)] for f in FILIALES]
    pd.DataFrame(ventas).to_excel(os.path.join(OUT, "ventas_presupuesto.xlsx"), index=False)
    print("✓ ageing de proveedores, compromisos, atrasos y ventas presupuestadas en datos/")


if __name__ == "__main__":
    main()
