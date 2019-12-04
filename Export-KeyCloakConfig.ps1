param(
    [string]$workingDir = $PSScriptRoot,
    [string]$composeFilePath = (Join-Path $PSScriptRoot 'docker-compose.yml')
)
. (Join-Path $workingDir "KeyCloakUtils.ps1")

try {
    Get-Command -ErrorAction Stop jq | Out-Null
}
catch [System.Management.Automation.CommandNotFoundException] {
    throw "jq (https://stedolan.github.io/jq/) is not on the path, but is required for proper operation. Please install with Chocolatey or Scoop and try again."
}

$importDir = Join-Path $workingDir "import"

Write-Host "Cleaning export destination."
if(Test-Path $importDir) { Remove-Item -Recurse -Force $importDir }
New-Item -ItemType Directory $importDir | Out-Null

Write-Host "Exporting KeyCloak configuration to $importDir."
Invoke-KeyCloakMigration -action "export" -composeFilePath $composeFilePath

Write-Host "Sorting export files."
Get-ChildItem $importDir | ForEach-Object {
    Get-Content $_.FullName | jq -S -f (Join-Path $workingDir "sortArrays.jq") | Set-Content $_.FullName
}
