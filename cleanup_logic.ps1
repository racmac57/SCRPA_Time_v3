# cleanup_logic.ps1
# This script handles the file cleanup and reporting logic.
# It is designed to be called by a .bat file.

param (
    [string]$ScriptsDir,
    [string]$ArchiveDir,
    [string]$MigrationBackupDir,
    [string]$DuplicateReportPath
)

# Step 1: Move Migration Backups
Write-Host "Step 1: Moving migration backup files..."
try {
    # Use the -LiteralPath parameter with Get-ChildItem for robustness
    $migrationFiles = Get-ChildItem -LiteralPath $ScriptsDir -Filter 'migration_backup_*.py' -Recurse
    if ($migrationFiles) {
        Write-Host "  Found $($migrationFiles.Count) migration backup files to move."
        foreach ($file in $migrationFiles) {
            # Prepending with \\?\ is the definitive way to handle long paths in Windows.
            $sourcePath = "\\?\$($file.FullName)"
            try {
                Write-Host "    Moving $($file.Name)"
                Move-Item -LiteralPath $sourcePath -Destination $MigrationBackupDir -Force -ErrorAction Stop
            } catch {
                Write-Host "[ERROR] Failed to move $($file.Name): $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "  No migration backup files found to move."
    }
} catch {
    Write-Host "[FATAL ERROR] Could not search for migration backups: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host "  Migration backup move operation completed."
Write-Host ""

# Step 2: Archive non-Arcpy files
Write-Host "Step 2: Archiving non-Arcpy Python files..."
try {
    $nonArcpyFiles = Get-ChildItem -LiteralPath $ScriptsDir -Filter '*.py' -Recurse | Where-Object { !(Select-String -Path $_.FullName -Pattern 'import arcpy' -Quiet) }
    if ($nonArcpyFiles) {
        Write-Host "  Found $($nonArcpyFiles.Count) non-Arcpy files to archive."
        foreach ($file in $nonArcpyFiles) {
            $sourcePath = "\\?\$($file.FullName)"
            try {
                Write-Host "    Moving non-Arcpy file $($file.Name)"
                Move-Item -LiteralPath $sourcePath -Destination $ArchiveDir -Force -ErrorAction Stop
            } catch {
                Write-Host "[ERROR] Failed to move $($file.Name): $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "  No non-Arcpy files found to archive."
    }
} catch {
    Write-Host "[FATAL ERROR] Could not search for non-Arcpy files: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host "  Non-Arcpy archive operation completed."
Write-Host ""

# Step 3: Generate duplicate report
Write-Host "Step 3: Generating duplicate report..."
try {
    if (Test-Path $DuplicateReportPath) {
        Remove-Item $DuplicateReportPath
    }
    $duplicates = Get-ChildItem -LiteralPath $ScriptsDir -Recurse -Filter '*.py' |
                  Group-Object -Property Name |
                  Where-Object { $_.Count -gt 1 } |
                  ForEach-Object { $_.Group | Sort-Object LastWriteTime -Descending | Select-Object -Skip 1 } |
                  Select-Object -ExpandProperty FullName

    if ($duplicates) {
        $duplicates | Out-File -FilePath $DuplicateReportPath -Encoding UTF8
        Write-Host "  Duplicate report created: $DuplicateReportPath"
    } else {
        Write-Host "  No duplicates found in cleaned 01_scripts directory."
    }
} catch {
    Write-Host "[FATAL ERROR] Could not generate duplicate report: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""
