# Simple KGG to MP3 Converter
# Converts .kgg files to .mp3 format

Clear-Host
Write-Output "=== KGG to MP3 Converter ==="
Write-Output ""

# Check if kgg-dec.exe exists
if (-not (Test-Path "./kgg-dec.exe")) {
    Write-Output "ERROR: kgg-dec.exe not found"
    exit 1
}

# Check if ffmpeg.exe exists
if (-not (Test-Path "./kgm-vpr-out/ffmpeg.exe")) {
    Write-Output "ERROR: ffmpeg.exe not found in kgm-vpr-out folder"
    exit 1
}

# Create output directory if needed
if (-not (Test-Path "./kgm-vpr-out")) {
    New-Item -Path "./kgm-vpr-out" -ItemType Directory | Out-Null
    Write-Output "Created output directory: kgm-vpr-out"
}

# Find all .kgg files
$kggFiles = Get-ChildItem -Filter "*.kgg" -File

if ($kggFiles.Count -eq 0) {
    Write-Output "No .kgg files found"
    exit 0
}

Write-Output "Found $($kggFiles.Count) .kgg files, starting conversion:"
Write-Output ""

foreach ($kggFile in $kggFiles) {
    $baseName = $kggFile.BaseName
    Write-Output "Processing: $($kggFile.Name)"
    
    # Run kgg-dec.exe
    & "./kgg-dec.exe" $kggFile.FullName
    
    # Check if output file was created
    $tempOgg = "${baseName}_kgg-dec.ogg"
    if (Test-Path $tempOgg) {
        Write-Output "  ✓ kgg-dec conversion successful"
        
        # Rename to .ogg
        Rename-Item -Path $tempOgg -NewName "${baseName}.ogg" -Force
        Write-Output "  ✓ Renamed to ${baseName}.ogg"
        
        # Convert to MP3
        & "./kgm-vpr-out/ffmpeg.exe" -i "${baseName}.ogg" -q:a 0 -map_metadata 0 "./kgm-vpr-out/${baseName}.mp3" 2>$null
        
        if (Test-Path "./kgm-vpr-out/${baseName}.mp3") {
            Write-Output "  ✓ Successfully created ${baseName}.mp3"
            # Clean up temp file
            Remove-Item -Path "${baseName}.ogg" -Force
            Write-Output "  ✓ Removed temporary file"
        } else {
            Write-Output "  ✗ ffmpeg conversion failed"
        }
    } else {
        Write-Output "  ✗ kgg-dec conversion failed"
        Write-Output "    Possible reason: Missing decryption key. Please play this file with KuGou Music client first."
    }
    
    Write-Output ""
}

Write-Output "=== Conversion Complete ==="
Write-Output ""
Write-Output "Results are in: ./kgm-vpr-out"
Write-Output ""