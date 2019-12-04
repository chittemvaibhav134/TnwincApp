function Watch-Process {
    param (
        [Parameter(Mandatory=$true)]
        [string]$fileName,
        [Parameter(Mandatory=$true)]
        [string[]]$argumentList,
        [Parameter(Mandatory=$true)]
        [string]$watchForRegex,
        [int]$watchCountLimit = 1,
        [string]$description = "process",
        [bool]$showOutput = $false,
        [int]$timeoutSeconds = 60
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo -Property @{
        CreateNoWindow = $true;
        UseShellExecute = $false;
        RedirectStandardOutput = $true;
        RedirectStandardError = $true;
        FileName = $fileName;
        Arguments = $argumentList;
    }

    $process = New-Object System.Diagnostics.Process -Property @{ StartInfo = $psi }
    $process.Start() | Out-Null

    if (-not $showOutput) {Write-Host "Monitoring $description." -NoNewline}

    $startDate = Get-Date

    $watchCount = 0
    while ($watchCount -lt $watchCountLimit)
    {
        $line = $process.StandardOutput.ReadLine()
        while ($line)
        {
            if(((Get-Date).Subtract($startDate)).TotalSeconds -gt $timeoutSeconds)
            {
                throw "Timeout of $timeoutSeconds seconds exceeded. Aborting."
            }

            if ($showOutput) {Write-Host $line}
            if ($line -match $watchForRegex)
            {
                $watchCount++
                break
            }
            $line = $process.StandardOutput.ReadLine()
        }
        if (-not $showOutput) {Write-Host "." -NoNewline}
        Start-Sleep -Seconds 1
    }

    if (-not $showOutput) {Write-Host "done."}

    $process.Close() | Out-Null
}


