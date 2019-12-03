param(
    $workingDir = (Get-Location).Path
)
. ./KeyCloakUtils.ps1

try {
    Get-Command -ErrorAction Stop jq > $null
}
catch [System.Management.Automation.CommandNotFoundException] {
    Write-Error "jq (https://stedolan.github.io/jq/) is not on the path, but is required for proper operation. Please install with Chocolatey or Scoop and try again."
    exit
}

$importDir = [System.IO.Path]::Combine($workingDir, "import")

Write-Host "Cleaning export destination."
if(Test-Path $importDir) { Remove-Item -Recurse -Force $importDir }
New-Item -ItemType Directory $importDir > $null

Restart-KeyCloak

Write-Host "Starting export."
Watch-KeyCloak -argumentList "exec", "-it", "keycloak-app", "/opt/jboss/tools/docker-entrypoint.sh", "`"-Djboss.socket.binding.port-offset=100 -Dkeycloak.migration.action=export -Dkeycloak.migration.provider=dir -Dkeycloak.migration.dir=/import`""
Write-Host "Finished export."

Restart-KeyCloak

Write-Host "Sorting export files."
[System.IO.Directory]::GetFiles($importDir) `
    | ForEach-Object {
        $inputFilePath = $_
        $outputFilePath = [System.IO.Path]::Combine([System.IO.Path]::GetDirectoryName($inputFilePath), [System.IO.Path]::GetRandomFileName())

        # sort JSON
        $originalOutFileEncoding = $PSDefaultParameterValues['Out-File:Encoding'] # so we can restore the original value when we're done
        $PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
        Get-Content $inputFilePath | jq -S -f .\sortArrays.jq > $outputFilePath # UTF-8, but still has a BOM
        $PSDefaultParameterValues['Out-File:Encoding'] = $originalOutFileEncoding

        # strip BOM
        $encoding = New-Object System.Text.UTF8Encoding $false
        $content = Get-Content $outputFilePath
        [System.IO.File]::WriteAllLines($outputFilePath, $content, $encoding)

        Remove-Item $inputFilePath
        Rename-Item $outputFilePath $inputFilePath
    }
