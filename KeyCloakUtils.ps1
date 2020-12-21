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
        "-Dkeycloak.migration.dir=/import"
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

    Restart-KeyCloak -composeFilePath $composeFilePath -showOutput $showOutput
}

function Restart-KeyCloak {
    param (
        [Parameter(Mandatory = $true)]
        [string]$composeFilePath,
        [bool]$showOutput
    )

    Write-Host "Restarting KeyCloak."
    docker-compose -f $composeFilePath down
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

    Watch-Process -showOutput $showOutput -fileName "docker" -argumentList $argumentList -watchForRegex "Admin console listening on" -watchCountLimit 1 -description "KeyCloak start"
}
