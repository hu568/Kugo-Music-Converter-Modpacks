# FLAC to KGM Renamer
# Renames .flac files to .kgm files

Clear-Host
Write-Output "=== FLAC to KGM File Renamer ==="
Write-Output ""

# Set file extensions
$sourceExt = ".flac"
$targetExt = ".kgm"

# Initialize counters
$successCount = 0
$skipCount = 0
$errorCount = 0

# Find all .flac files
$flacFiles = Get-ChildItem -Filter "*$sourceExt" -File

if ($flacFiles.Count -eq 0) {
    Write-Output "No .flac files found"
    exit 0
}

Write-Output "Found $($flacFiles.Count) .flac files, starting renaming:"
Write-Output ""

foreach ($flacFile in $flacFiles) {
    $baseName = $flacFile.BaseName
    $targetName = "${baseName}$targetExt"
    
    Write-Output "Processing: $($flacFile.Name)"
    
    # Check if target file already exists
    if (Test-Path $targetName) {
        Write-Output "  ⚠️  Skipped: $targetName already exists"
        $skipCount++
    } else {
        # Try to rename the file
        try {
            Rename-Item -Path $flacFile.FullName -NewName $targetName -Force
            Write-Output "  ✓ Renamed: $($flacFile.Name) -> $targetName"
            $successCount++
        } catch {
            Write-Output "  ✗ Error: Failed to rename $($flacFile.Name)"
            $errorCount++
        }
    }
    
    Write-Output ""
}

# Show summary
Write-Output "=== Renaming Summary ==="
Write-Output "Successfully renamed: $successCount files"
Write-Output "Skipped (already exists): $skipCount files"
Write-Output "Failed: $errorCount files"
Write-Output ""

if ($errorCount -eq 0 -and $skipCount -eq 0) {
    Write-Output "✅ All files were successfully renamed!"
} elseif ($errorCount -eq 0) {
    Write-Output "✅ All renaming operations completed, some files were skipped."
} else {
    Write-Output "⚠️  Renaming completed with some errors."
}

Write-Output ""