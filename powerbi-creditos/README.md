# Dashboard de créditos en Power BI (datos ficticios)

Antes de automatizar el [informe mensual](../informe-mensual), el seguimiento de créditos vivía en un dashboard de Power BI. Funcionaba bien, pero actualizarlo llevaba seis pasos manuales cada mes: renombrar archivos, pegar exportaciones, borrar columnas, marcar cada fila como "OVERDUE" o "RECEIVABLE"...

Esta carpeta genera los Excel de carga de ese dashboard **con datos ficticios** (Distribuidora Papel, los mismos clientes que el resto de las demos), con las mismas hojas y columnas que los exports estándar de SAP:

| Hoja | Qué tiene |
|---|---|
| `CONSOLIDADO OVERDUE+RCV` | Partidas abiertas de clientes al cierre (FBL5N), marcadas `OVERDUE` o `RECEIVABLE M` |
| `CONSOLIDADO INV+RCV` | Cobrables de M y M-1 más 5 meses de facturación (`INVOICING`), para el DSO |
| `FBL3N LAYOUT RAPPELS` | Abonos por rappel, para separarlos del vencido |
| `DELEGACIONES-BRANCH` | Delegación → branch → país |

```
python generar_excel.py
```

Requiere haber corrido antes `informe-mensual/generar_datos.py` (de ahí salen las facturas).

## Usarlos en un .pbix existente

1. Abrir el `.pbix` en Power BI Desktop.
2. **Transformar datos → Configuración de origen de datos**.
3. Elegir cada origen (`OVERDUE y DSO TEMPLATE.xlsx` y `... M-1.xlsx`) → **Cambiar origen** → apuntar a la carpeta `datos/` de este proyecto.
4. **Cerrar y aplicar**, y después **Actualizar**.

Si algún visual queda en blanco, lo más probable es que el modelo filtre por un código de sociedad o un nombre de branch fijo; en este set las sociedades son `DE10`, `NL10`, `BE10`, `AT10` y los branches `GERMANY/NETHERLANDS/BELGIUM/AUSTRIA DISTRIBUTION`.

> Todos los datos son ficticios.
