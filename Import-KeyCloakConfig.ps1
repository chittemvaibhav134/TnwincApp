param(
    [string]$workingDir = $PSScriptRoot,
    [string]$composeFilePath = (Join-Path $PSScriptRoot 'docker-compose.yml')
)
. (Join-Path $workingDir "KeyCloakUtils.ps1")

Write-Host "Importing KeyCloak config from $(Join-Path $workingDir 'import')."
Invoke-KeyCloakMigration -action "import" -composeFilePath $composeFilePath
