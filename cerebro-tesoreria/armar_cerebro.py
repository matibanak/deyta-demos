# -*- coding: utf-8 -*-
"""
Cortex: un "cerebro" de tesorería que conecta los dashboards de las otras demos.

No recalcula nada: lee lo que cada pieza ya generó (los datos embebidos en cada HTML
y el metricas.json del informe), arma las alertas cruzadas y prepara las respuestas
a las preguntas típicas. En la versión real, las preguntas las responde Claude
usando estos mismos datos como contexto.

Requiere haber corrido antes las demos: informe-mensual, saldos-tesoreria,
forecast-caja, conciliacion y grupo-neto.
Salida: Cortex.html
"""
import os
import sys
import json
import datetime as dt

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(BASE)
FUENTES = {
    "informe": "informe-mensual/metricas.json",
    "saldos": "saldos-tesoreria/Saldos_tesoreria.html",
    "forecast": "forecast-caja/Forecast_13_semanas.html",
    "conciliacion": "conciliacion/salida/informe.html",
    "grupo": "grupo-neto/Grupo_neto.html",
}


def leer(nombre):
    ruta = os.path.join(RAIZ, FUENTES[nombre])
    if not os.path.exists(ruta):
        sys.exit(f"Falta {FUENTES[nombre]}: corré primero esa demo.")
    texto = open(ruta, encoding="utf-8").read()
    if ruta.endswith(".json"):
        return json.loads(texto)
    inicio = texto.index("const D = ") + len("const D = ")
    return json.JSONDecoder().raw_decode(texto[inicio:])[0]


def k(v):
    return f"{v / 1e3:,.0f} k€".replace(",", ".").replace("-", "−")


def M(v):
    return f"{v / 1e6:,.2f} M€".replace(",", "X").replace(".", ",").replace("X", ".")


def fecha(iso):
    d = dt.date.fromisoformat(iso[:10])
    return f"{['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'][d.weekday()]} {d:%d/%m}"


def main():
    inf, sal, fc, con, gru = (leer(n) for n in FUENTES)
    gn = gru["fotos"][max(gru["fotos"])]
    cli = inf["clientes"][0]
    tot = inf["resumen"]["Total"]
    alerta_saldo = sal["alertas"][0] if sal["alertas"] else None
    base, sin = fc["escenarios"]["base"], fc["escenarios"]["sin_cliente"]
    i_min_sin = sin["saldo"].index(min(sin["saldo"]))
    pos_be = gn["posicion"]["BE10"]
    pend_motivos = {}
    for p in con["pend"]:
        clave = "sin contrapartida" if p["Motivo"].startswith("Sin") else "diferencia mínima" if p["Motivo"].startswith("Diferencia") else "fuera de plazo"
        pend_motivos[clave] = pend_motivos.get(clave, 0) + 1

    nodos = [
        {"id": "informe", "titulo": "Créditos", "dato": f"{tot['pct_vencido']:.1f} % vencido".replace(".", ","),
         "detalle": f"{cli['cliente']}: {k(cli['vencido'])} vencidos", "alerta": True, "demo": "informe-mensual"},
        {"id": "saldos", "titulo": "Saldos", "dato": f"{len(sal['alertas'])} cuenta en negativo",
         "detalle": f"{alerta_saldo['cuenta']} el {fecha(alerta_saldo['fecha'])}" if alerta_saldo else "sin alertas",
         "alerta": bool(alerta_saldo), "demo": "saldos-tesoreria"},
        {"id": "forecast", "titulo": "Forecast", "dato": f"mínimo {M(min(base['saldo']))}",
         "detalle": f"sin {fc['cliente_escenario']}: {M(min(sin['saldo']))}", "alerta": min(sin["saldo"]) < fc["colchon"], "demo": "forecast-caja"},
        {"id": "conciliacion", "titulo": "Conciliación", "dato": f"{round(con['conciliadas'] / con['total'] * 100)} % automático",
         "detalle": f"{con['pendientes']} partidas pendientes", "alerta": False, "demo": "conciliacion"},
        {"id": "grupo", "titulo": "Grupo", "dato": f"neto {M(gn['multilateral_total'])}",
         "detalle": f"Bélgica debe {k(-pos_be)} al grupo", "alerta": pos_be < 0, "demo": "grupo-neto"},
    ]

    alertas = [
        f"{cli['cliente']} ({cli['filial']}) concentra {k(cli['vencido'])} vencidos, el {cli['vencido'] / tot['vencido'] * 100:.0f} % del grupo.",
        f"La cuenta {alerta_saldo['cuenta']} ({alerta_saldo['filial']}) entra en negativo el {fecha(alerta_saldo['fecha'])}: {k(alerta_saldo['minimo'])}." if alerta_saldo else None,
        f"Si {fc['cliente_escenario']} no paga, la caja cae a {M(sin['saldo'][i_min_sin])} en la semana del {fc['desde'][i_min_sin][8:10]}/{fc['desde'][i_min_sin][5:7]}, debajo del colchón de {M(fc['colchon'])}.",
        f"Bélgica le debe {k(-pos_be)} netos al resto del grupo.",
    ]
    alertas = [a for a in alertas if a]

    preguntas = [
        {"q": "¿Qué cuentas van a quedar en negativo?",
         "a": [f"{a['cuenta']} ({a['filial']} · {a['banco']}): entra en negativo el {fecha(a['fecha'])} y llega a {k(a['minimo'])}." for a in sal["alertas"]]
              or ["Ninguna en los próximos 10 días hábiles."],
         "fuente": "Saldos de tesorería"},
        {"q": "¿Qué clientes están atrasados y por cuánto?",
         "a": [f"{c['cliente']} ({c['filial']}): {k(c['vencido'])} vencidos" + (f", {k(c['31-60'])} con más de 30 días." if c["31-60"] else ".")
               for c in inf["clientes"][:4] if c["vencido"]],
         "fuente": f"Informe de crédito · {inf['mes']}"},
        {"q": "¿Cuándo es el punto más bajo de caja?",
         "a": [f"Escenario base: {M(min(base['saldo']))}, en la semana {base['saldo'].index(min(base['saldo'])) + 1}.",
               f"Si {fc['cliente_escenario']} no paga: {M(min(sin['saldo']))}, debajo del colchón de {M(fc['colchon'])}."],
         "fuente": "Forecast de caja a 13 semanas"},
        {"q": "¿Cuánto le debe cada filial al grupo?",
         "a": [f"{gru['sociedades'][c]}: {'le debe' if v < 0 else 'le deben'} {k(abs(v))}." for c, v in sorted(gn["posicion"].items(), key=lambda x: x[1])],
         "fuente": "Deuda entre sociedades"},
        {"q": "¿Qué quedó sin conciliar?",
         "a": [f"{con['pendientes']} de {con['total']} partidas, por {k(con['importe_pend'])}."] + [f"{n} por {m}." for m, n in pend_motivos.items()],
         "fuente": "Conciliación automática"},
        {"q": "¿Qué tienen en común todas las alertas?",
         "a": [f"Casi todas llevan a {cli['cliente']}.",
               f"Su deuda vencida explica el {cli['vencido'] / tot['vencido'] * 100:.0f} % del vencido del grupo; sin sus cobros, la cuenta de Bélgica entra en negativo, el forecast cruza el colchón y Bélgica se financia con deuda del grupo.",
               "Una conversación con ese cliente puede resolver cuatro alertas a la vez."],
         "fuente": "Cruce de los cinco tableros"},
    ]

    data = {"empresa": "Distribuidora Papel", "fecha": "2026-11-02", "nodos": nodos, "alertas": alertas, "preguntas": preguntas}
    html = open(os.path.join(BASE, "plantilla.html"), encoding="utf-8").read().replace(
        "/*__DATOS__*/null", json.dumps(data, ensure_ascii=False))
    open(os.path.join(BASE, "Cortex.html"), "w", encoding="utf-8").write(html)
    print(f"✓ Cortex.html — {len(nodos)} tableros conectados, {len(alertas)} alertas, {len(preguntas)} preguntas")


if __name__ == "__main__":
    main()
