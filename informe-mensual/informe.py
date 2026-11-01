# -*- coding: utf-8 -*-
"""
Corre el informe del mes completo, de punta a punta:

  1. (solo la primera vez) genera los datos ficticios en datos/
  2. calcular.py          -> metricas.json
  3. generar_informe.js   -> salida/Informe_credito_AAAA-MM.pptx
  4. exportar_png.ps1     -> una imagen por slide (solo Windows con PowerPoint)

Uso: python informe.py [AAAA-MM]
"""
import os
import sys
import json
import shutil
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
PY = sys.executable


def paso(n, texto, cmd):
    print(f"\n[{n}] {texto}")
    subprocess.run(cmd, check=True)


if not os.path.isdir("datos"):
    paso(0, "Generando datos ficticios", [PY, "generar_datos.py"])

paso(1, "Calculando métricas", [PY, "calcular.py", *sys.argv[1:2]])

periodo = json.load(open("metricas.json", encoding="utf-8"))["periodo"]
pptx = os.path.join("salida", f"Informe_credito_{periodo}.pptx")
paso(2, "Armando el PowerPoint", ["node", "generar_informe.js", "metricas.json", pptx])

if os.name == "nt" and shutil.which("powershell"):
    paso(3, "Exportando slides a PNG", ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                                        "-File", "exportar_png.ps1", pptx])

print(f"\n✓ Listo: {pptx}")
