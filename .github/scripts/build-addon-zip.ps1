param(
    [Parameter(Mandatory = $true)]
    [string]$AddonDirectory,

    [Parameter(Mandatory = $true)]
    [string]$Destination
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$addonRoot = (Resolve-Path -LiteralPath $AddonDirectory).Path
[xml]$addonXml = Get-Content -LiteralPath (Join-Path $addonRoot 'addon.xml') -Raw
$addonId = [string]$addonXml.addon.id
$version = [string]$addonXml.addon.version
if ([string]::IsNullOrWhiteSpace($addonId) -or [string]::IsNullOrWhiteSpace($version)) {
    throw 'addon.xml must define an add-on ID and version.'
}

$destinationDirectory = Split-Path -Parent $Destination
New-Item -ItemType Directory -Force -Path $destinationDirectory | Out-Null
if (Test-Path -LiteralPath $Destination) {
    Remove-Item -LiteralPath $Destination -Force
}

$zip = [System.IO.Compression.ZipFile]::Open(
    $Destination,
    [System.IO.Compression.ZipArchiveMode]::Create
)
try {
    Get-ChildItem -LiteralPath $addonRoot -Recurse -File | Sort-Object FullName | ForEach-Object {
        $relativePath = $_.FullName.Substring($addonRoot.Length).TrimStart([char]92, [char]47)
        $normalizedPath = $relativePath -replace '\\', '/'
        $segments = $normalizedPath -split '/'

        $hasHiddenSegment = @($segments | Where-Object { $_.StartsWith('.') }).Count -gt 0
        $hasExcludedDirectory = @($segments | Where-Object { $_ -in @('.git', '.github', '.vscode', '__pycache__', 'temp') }).Count -gt 0
        if ($hasHiddenSegment -or $hasExcludedDirectory) { return }
        if ($addonId -eq 'script.skinhelper.ping' -and $_.Name -in @('AGENTS.md', 'Projekt_Rules.md', 'ML.md', 'CLAUDE.md')) { return }
        if ($_.Name -like '*.pyc' -or $_.Name -like '*.pyo' -or $_.Name -like '*.log' -or $_.Name -in @('Thumbs.db', '.DS_Store')) { return }

        $entry = $zip.CreateEntry("$addonId/$normalizedPath", [System.IO.Compression.CompressionLevel]::Optimal)
        $entryStream = $entry.Open()
        $fileStream = [System.IO.File]::OpenRead($_.FullName)
        try {
            $fileStream.CopyTo($entryStream)
        }
        finally {
            $fileStream.Dispose()
            $entryStream.Dispose()
        }
    }
}
finally {
    $zip.Dispose()
}

Write-Host "Created $Destination"
