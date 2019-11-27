param(
    $workingDir = (Get-Location).Path
)
. ./Watch-Process.ps1

$importDir = [System.IO.Path]::Combine($workingDir, "import")

Write-Host "Cleaning export destination."
if(Test-Path $importDir) { Remove-Item -Recurse -Force $importDir }
if(Test-Path .\export-stdout.log) { Remove-Item -Force .\export-stdout.log }
New-Item -ItemType Directory $importDir > $null

Write-Host "Restarting KeyCloak for a clean export."
docker-compose down
docker-compose up -d
$filePath = "docker"
$argumentList = "logs", "-f", "keycloak-app"
$watchForString = "Keycloak 8.0.0 (WildFly Core 10.0.0.Final) started"
$watchCountLimit = 3
Watch-Process $filePath $argumentList $watchForString $watchCountLimit "KeyCloak restart"
Write-Host "Finished KeyCloak restart."

Write-Host "Starting export."
$argumentList = "exec", "-it", "keycloak-app", "/opt/jboss/tools/docker-entrypoint.sh", "`"-Djboss.socket.binding.port-offset=100 -Dkeycloak.migration.action=export -Dkeycloak.migration.provider=dir -Dkeycloak.migration.dir=/import`""
Watch-Process $filePath $argumentList $watchForString $watchCountLimit "KeyCloak export"
Write-Host "Finished export."

Write-Host "Restarting KeyCloak without waiting."
docker-compose down
docker-compose up -d

Write-Host "Sorting export files."
[System.IO.Directory]::GetFiles($importDir) `
    | ForEach-Object {
        $inputFilePath = $_
        $outputFilePath = [System.IO.Path]::Combine([System.IO.Path]::GetDirectoryName($inputFilePath), [System.IO.Path]::GetRandomFileName())

        # sort JSON
        $PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
        Get-Content $inputFilePath | jq -S -f .\sortArrays.jq > $outputFilePath # UTF-8, but still has a BOM

        # strip BOM
        $encoding = New-Object System.Text.UTF8Encoding $false
        $content = Get-Content $outputFilePath
        [System.IO.File]::WriteAllLines($outputFilePath, $content, $encoding)

        Remove-Item $inputFilePath
        Rename-Item $outputFilePath $inputFilePath
    }
