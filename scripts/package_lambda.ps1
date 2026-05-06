param(
    [string]$RootDir = (Resolve-Path "$PSScriptRoot\.."),
    [string]$ArtifactDir = "dist"
)

$fullArtifactDir = Join-Path $RootDir $ArtifactDir
$packageDir = Join-Path $fullArtifactDir "lambda_package"

if (Test-Path $packageDir) {
    Remove-Item -Recurse -Force $packageDir
}

New-Item -ItemType Directory -Force -Path $packageDir | Out-Null
python -m pip install -r (Join-Path $RootDir "requirements.txt") -t $packageDir
Copy-Item -Recurse -Path (Join-Path $RootDir "src\\otimizador") -Destination $packageDir

$zipPath = Join-Path $fullArtifactDir "otimizador-lambda.zip"
if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}

Compress-Archive -Path (Join-Path $packageDir "*") -DestinationPath $zipPath
Write-Host "Artifact: $zipPath"
