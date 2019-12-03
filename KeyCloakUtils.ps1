. ./Watch-Process.ps1
function Restart-KeyCloak {
    param (
        [string]$containerName = "keycloak-app"
    )

    Write-Host "Restarting KeyCloak."
    docker-compose down
    docker-compose up -d
    Watch-KeyCloak -argumentList "logs", "-f", $containerName
    Write-Host "Finished KeyCloak restart."
}

function Watch-KeyCloak {
    param (
        [string]$filePath = "docker",
        [string[]]$argumentList,
        [string]$watchForRegEx = "Keycloak \d\.\d\.\d \(WildFly Core \d+\.\d\.\d\.Final\) started",
        [int]$watchCountLimit = 3
    )
    Watch-Process $filePath $argumentList $watchForRegEx $watchCountLimit "KeyCloak start"
}
