function Watch-Process {
    param (
        [string]$fileName,
        [string[]]$argumentList,
        [string]$watchForRegex,
        [int]$watchCountLimit,
        [string]$description = "process",
        [bool]$showOutput = $false
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo -Property @{
        CreateNoWindow = $true;
        UseShellExecute = $false;
        RedirectStandardOutput = $true;
        RedirectStandardError = $true;
        FileName = $filePath;
        Arguments = $argumentList;
    }

    $process = New-Object System.Diagnostics.Process -Property @{ StartInfo = $psi }
    $process.Start() > $null

    if (-not $showOutput) {Write-Host "Monitoring $description." -NoNewline}

    $watchCount = 0
    while ($watchCount -lt $watchCountLimit)
    {
        while ($null -ne ($line = $process.StandardOutput.ReadLine()))
        {
            if ($showOutput) {Write-Host $line}
            if ($line -match $watchForRegex)
            {
                $watchCount++
                break
            }
        }
        if (-not $showOutput) {Write-Host "." -NoNewline}
        Start-Sleep -Seconds 1
    }

    if (-not $showOutput) {Write-Host "done."}

    $process.Close() > $null
}


