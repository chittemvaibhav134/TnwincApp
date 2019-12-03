param(
    $workingDir = (Get-Location).Path
)
. ./KeyCloakUtils.ps1

Restart-KeyCloak

Write-Host "Starting import."
Watch-KeyCloak -argumentList "exec", "-it", "keycloak-app", "/opt/jboss/tools/docker-entrypoint.sh", "`"-Djboss.socket.binding.port-offset=100 -Dkeycloak.migration.action=import -Dkeycloak.migration.provider=dir -Dkeycloak.migration.dir=/import`""
Write-Host "Finished import."

Restart-KeyCloak
