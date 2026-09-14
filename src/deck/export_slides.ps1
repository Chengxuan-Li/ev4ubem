# Export every slide of the deck to PNG with Microsoft PowerPoint (Windows, visual QA only).
# Usage (repo root): powershell -ExecutionPolicy Bypass -File src/deck/export_slides.ps1 [-Deck results/deck/ev4ubem_model_deck.pptx] [-Out results/deck/png]
param(
    [string]$Deck = "results/deck/ev4ubem_model_deck.pptx",
    [string]$Out = "results/deck/png",
    [int]$Width = 1920
)
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$deckPath = (Resolve-Path (Join-Path $root $Deck)).Path
$outPath = Join-Path $root $Out
New-Item -ItemType Directory -Force $outPath | Out-Null
Get-ChildItem $outPath -Filter "slide_*.png" -ErrorAction SilentlyContinue | Remove-Item -Force
$app = New-Object -ComObject PowerPoint.Application
try {
    # Open(FileName, ReadOnly, Untitled, WithWindow)
    $pres = $app.Presentations.Open($deckPath, -1, 0, 0)
    $h = [int]($Width * $pres.PageSetup.SlideHeight / $pres.PageSetup.SlideWidth)
    foreach ($s in $pres.Slides) {
        $file = Join-Path $outPath ("slide_{0:D2}.png" -f $s.SlideIndex)
        $s.Export($file, "PNG", $Width, $h)
    }
    "exported $($pres.Slides.Count) slides to $outPath"
    $pres.Close()
}
finally {
    $app.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
}
