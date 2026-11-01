# Deyta · demos

Versiones de demostración de sistemas de datos que armé para finanzas y tesorería: informes que se generan solos, dashboards que se actualizan con un click, conciliaciones automáticas.

Cada carpeta es un proyecto independiente, con su propio README. **El código está reescrito desde cero y todos los datos son ficticios**: la empresa de los ejemplos, "Distribuidora Papel", no existe.

| Proyecto | Qué resuelve |
|---|---|
| [forecast-caja](forecast-caja) | Forecast de caja a 13 semanas, con cobros en la fecha en que cada cliente paga de verdad y escenarios. |
| [grupo-neto](grupo-neto) | Deuda entre sociedades del grupo: matriz bruta, neteo bilateral y multilateral, con histórico diario. |
| [informe-mensual](informe-mensual) | El informe de crédito del mes, del export del ERP al PowerPoint con un comando. |
| [cerebro-tesoreria](cerebro-tesoreria) | Cortex: conecta todos los tableros, cruza las alertas y responde preguntas con los datos del día. |
| [conciliacion](conciliacion) | Empareja partidas abiertas (1:1, 1:N, N:1) y explica por qué no cuadra cada pendiente. |
| [powerbi-creditos](powerbi-creditos) | Excel de carga con datos ficticios para un dashboard de créditos en Power BI. |
| [saldos-tesoreria](saldos-tesoreria) | El saldo de cada banco proyectado a 10 días, con alerta cuando una cuenta va a quedar en negativo. |

Todas las demos usan la misma empresa ficticia, así que sus historias se conectan: un cliente que deja de pagar aparece en el informe de crédito, deja una cuenta en negativo, mueve el forecast y termina explicando casi todas las alertas de Cortex.

---

Matías Banak · [Deyta Analytics](https://deyta-web.web.app) · [@deyta.analytics](https://instagram.com/deyta.analytics)
