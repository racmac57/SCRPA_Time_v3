<#
.SYNOPSIS
    Update Power BI PBIX mashup parameter values programmatically using PowerShell.

.DESCRIPTION
    Extracts the PBIX (ZIP archive), locates the DataMashup file, updates the specified 'let' parameter,
    and repacks to a new PBIX file.

.PARAMETER Input
    Path to the input .pbix file.

.PARAMETER Output
    Path where the updated .pbix will be saved.

.PARAMETER Param
    Name of the mashup parameter to update.

.PARAMETER Value
    New value for the parameter.

# Artifact: update_pbix_parameter.ps1
# Timestamp: 2025-07-26 18:00:00 EST
# Project: SCRPA_Time_v2
# Author: R. A. Carucci
# Purpose: Update PBIX mashup parameter values programmatically with PowerShell
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$Input,

    [Parameter(Mandatory=$true)]
    [string]$Output,

    [Parameter(Mandatory=$true)]
    [string]$Param,

    [Parameter(Mandatory=$true)]
    [string]$Value
)

# Validate input file
if (-not (Test-Path -Path $Input -PathType Leaf)) {
    Write-Error "Input file not found: $Input"
    exit 1
}

# Create a temporary extraction directory
$tempDir = Join-Path -Path ([System.IO.Path]::GetTempPath()) -ChildPath ([System.IO.Path]::GetRandomFileName())
New-Item -ItemType Directory -Path $tempDir | Out-Null

try {
    # Extract all contents of the PBIX (ZIP archive)
    Expand-Archive -LiteralPath $Input -DestinationPath $tempDir -Force

    # Locate the DataMashup file (case-insensitive match)
    $mashupFile = Get-ChildItem -Path $tempDir -Recurse -File |
        Where-Object { $_.Name -imatch '^DataMashup' } |
        Select-Object -First 1

    if (-not $mashupFile) {
        throw "Could not locate any DataMashup file under $tempDir"
    }
    Write-Host "Using mashup file: $($mashupFile.FullName.Substring($tempDir.Length + 1))"

    # Read file bytes and decode with Latin1
    $bytes = [System.IO.File]::ReadAllBytes($mashupFile.FullName)
    $text  = [System.Text.Encoding]::GetEncoding('ISO-8859-1').GetString($bytes)

    # Pattern to match: let Param = "..."
    $escapedParam = [Regex]::Escape($Param)
    $pattern = "(?i)(let\s+${escapedParam}\s*=\s*)\"[^\"]*\""
    $replacement = "`$1`"$Value`""

    # Perform the replacement
    $updated = [System.Text.RegularExpressions.Regex]::Replace($text, $pattern, $replacement)

    # Encode back to bytes and overwrite
    $newBytes = [System.Text.Encoding]::GetEncoding('ISO-8859-1').GetBytes($updated)
    [System.IO.File]::WriteAllBytes($mashupFile.FullName, $newBytes)

    # Repack the directory into the output PBIX
    if (Test-Path -LiteralPath $Output) { Remove-Item -LiteralPath $Output -Force }
    Compress-Archive -Path "$tempDir\*" -DestinationPath $Output -Force
    Write-Host "Updated PBIX saved to: $Output"
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
finally {
    # Clean up temp directory
    Remove-Item -LiteralPath $tempDir -Recurse -Force
}
