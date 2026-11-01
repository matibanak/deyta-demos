# Exporta cada slide de un .pptx a PNG usando PowerPoint (Windows).
# Uso: powershell -File exportar_png.ps1 salida\Informe_credito_2026-10.pptx
param([Parameter(Mandatory = $true)][string]$Pptx, [int]$Ancho = 1920)

$ruta = (Resolve-Path $Pptx).Path
$destino = Join-Path (Split-Path $ruta) ([IO.Path]::GetFileNameWithoutExtension($ruta))
New-Item -ItemType Directory -Force $destino | Out-Null

$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($ruta, $true, $false, $false)  # solo lectura, sin ventana
$alto = [int]($Ancho * $pres.PageSetup.SlideHeight / $pres.PageSetup.SlideWidth)
foreach ($s in $pres.Slides) {
    $s.Export((Join-Path $destino ("slide-{0:D2}.png" -f $s.SlideIndex)), "PNG", $Ancho, $alto)
}
$pres.Close()
$app.Quit()
Write-Output "OK $destino"
