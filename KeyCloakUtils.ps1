. (Join-Path $PSScriptRoot "Watch-Process.ps1")

function Invoke-KeyCloakMigration {
    
    param (
        [Parameter(Mandatory = $true)]
        [ValidateSet("import", "export")]
        [string]$action,
        [Parameter(Mandatory = $true)]
        [string]$composeFilePath,
        [bool]$showOutput,
        [string]$containerName
    )

    Write-Host "Starting another KeyCloak instance with migration action [$action]."
    $systemProps = @(
        '-Djboss.socket.binding.port-offset=100',
        "-Dkeycloak.migration.action=$action",
        '-Dkeycloak.migration.provider=dir',
        "-Dkeycloak.migration.dir=/import/$containerName"
    )
    if ($action -eq 'export') {
        $systemProps += '-Dkeycloak.migration.usersExportStrategy=REALM_FILE'
    }
    $systemPropsQuoteEncapsulated = '"{0}"' -f ($systemProps -join ' ')
    $argumentList = @(
        'exec',
        '-it',
        $containerName,
        'opt/jboss/tools/docker-entrypoint.sh',
        "$systemPropsQuoteEncapsulated"
    )

    Wait-KeyCloakStartup -showOutput $showOutput -argumentList $argumentList

    Restart-KeyCloak $composeFilePath
}

function Restart-KeyCloak {
    param (
        [Parameter(Mandatory = $true)]
        [string]$composeFilePath,
        [bool]$showOutput
    )

    Write-Host "Restarting KeyCloak."
    docker-compose -f $composeFilePath rm -svf $containerName
    docker-compose -f $composeFilePath rm -svf "$containerName-db"
    docker-compose -f $composeFilePath up -d

    $argumentList = @(
        'logs',
        '-f',
        $containerName
    )
    
    Wait-KeyCloakStartup -showOutput $showOutput -argumentList $argumentList

    Write-Host "Finished KeyCloak restart."
}

function Wait-KeyCloakStartup {
    param (
        [Parameter(Mandatory = $true)]
        [string[]]$argumentList,
        [bool]$showOutput
    )

    Watch-Process -showOutput $showOutput -fileName "docker" -argumentList $argumentList -watchForRegex "Keycloak \d\.\d\.\d \(WildFly Core \d+\.\d\.\d\.Final\) started" -watchCountLimit 3 -description "KeyCloak start"
}
