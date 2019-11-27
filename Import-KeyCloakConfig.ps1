param(
    $workingDir = (Get-Location).Path
)
. ./Watch-Process.ps1

Write-Host "Restarting KeyCloak for a clean import."
docker-compose down
docker-compose up -d
$filePath = "docker"
$argumentList = "logs", "-f", "keycloak-app"
$watchForString = "Keycloak 8.0.0 (WildFly Core 10.0.0.Final) started"
$watchCountLimit = 3
Watch-Process $filePath $argumentList $watchForString $watchCountLimit "KeyCloak restart"
Write-Host "Finished KeyCloak restart."

Write-Host "Starting import."
$argumentList = "exec", "-it", "keycloak-app", "/opt/jboss/tools/docker-entrypoint.sh", "`"-Djboss.socket.binding.port-offset=100 -Dkeycloak.migration.action=import -Dkeycloak.migration.provider=dir -Dkeycloak.migration.dir=/import`""
Watch-Process $filePath $argumentList $watchForString $watchCountLimit "KeyCloak import"
Write-Host "Finished import."

Write-Host "Restarting KeyCloak without waiting."
docker-compose down
docker-compose up -d
