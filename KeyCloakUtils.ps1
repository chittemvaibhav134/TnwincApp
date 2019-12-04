. (Join-Path $PSScriptRoot "Watch-Process.ps1")

function Invoke-KeyCloakMigration {
    param (
        [Parameter(Mandatory=$true)]
        [ValidateSet("import", "export")]
        [string]$action,
        [Parameter(Mandatory=$true)]
        [string]$composeFilePath
    )

    Restart-KeyCloak $composeFilePath

    Write-Host "Starting another KeyCloak instance with migration action [$action]."
    $argumentList = @(
        'exec',
        '-it',
        'keycloak-app',
        'opt/jboss/tools/docker-entrypoint.sh',
        "`"-Djboss.socket.binding.port-offset=100 -Dkeycloak.migration.action=$action -Dkeycloak.migration.provider=dir -Dkeycloak.migration.dir=/import`""
    )

    Wait-KeyCloakStartup -argumentList $argumentList

    Restart-KeyCloak $composeFilePath
}

function Restart-KeyCloak {
    param (
        [Parameter(Mandatory=$true)]
        [string]$composeFilePath
    )

    Write-Host "Restarting KeyCloak."
    docker-compose -f $composeFilePath down
    docker-compose -f $composeFilePath up -d

    $argumentList = @(
        'logs',
        '-f',
        'keycloak-app'
    )
    Wait-KeyCloakStartup -argumentList $argumentList

    Write-Host "Finished KeyCloak restart."
}

function Wait-KeyCloakStartup {
    param (
        [Parameter(Mandatory=$true)]
        [string[]]$argumentList
    )

    Watch-Process -fileName "docker" -argumentList $argumentList -watchForRegex "Keycloak \d\.\d\.\d \(WildFly Core \d+\.\d\.\d\.Final\) started" -watchCountLimit 3 -description "KeyCloak start"
}
