# Read-only installed-file inventory. No executables, game tools or registry APIs run.
$ErrorActionPreference='Stop'
$researchRoot='C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\native-source-oracle-research-20261113'
$sfm='C:\Program Files (x86)\Steam\steamapps\common\SourceFilmmaker\game'
$gmod='C:\Program Files (x86)\Steam\steamapps\common\GarrysMod'
$output=Join-Path $researchRoot ('inventory-'+[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()+'.json')
if (Test-Path -LiteralPath $output) { throw 'Fresh inventory output required' }
$selected=@(
    (Join-Path $sfm 'sfm.exe'),
    (Join-Path $sfm 'bin\hlmv.exe'),
    (Join-Path $sfm 'bin\hlfaceposer.exe'),
    (Join-Path $sfm 'bin\studiomdl.exe'),
    (Join-Path $sfm 'bin\sdktemplates\content\run_hlmv_template.bat'),
    (Join-Path $sfm 'usermod\gameinfo.txt'),
    (Join-Path $sfm 'tf_movies\gameinfo.txt'),
    (Join-Path $sfm 'tf\gameinfo.txt'),
    (Join-Path $sfm 'left4dead2_movies\gameinfo.txt'),
    (Join-Path $sfm 'hl2\gameinfo.txt'),
    (Join-Path $gmod 'garrysmod\gameinfo.txt'),
    (Join-Path $gmod 'bin\hlmv.exe'),
    (Join-Path $gmod 'bin\win64\hlmv.exe'),
    (Join-Path $gmod 'bin\hlfaceposer.exe'),
    (Join-Path $gmod 'bin\studiomdl.exe'),
    (Join-Path $gmod 'bin\win64\studiomdl.exe')
)
foreach ($folder in @((Join-Path $sfm 'bin'),(Join-Path $gmod 'bin'),(Join-Path $gmod 'bin\win64'))) {
    foreach ($name in @('materialsystem.dll','shaderapidx9.dll','stdshader_dx9.dll','filesystem_stdio.dll','studiorender.dll','datacache.dll','tier0.dll','vstdlib.dll','game_shader_generic_garrysmod.dll')) {
        $selected+=Join-Path $folder $name
    }
}
$records=@()
foreach ($path in $selected) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $records+=[ordered]@{path=$path;exists=$false}
        continue
    }
    $file=Get-Item -LiteralPath $path
    $before=[ordered]@{bytes=$file.Length;mtime_utc=$file.LastWriteTimeUtc.ToString('o');sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
    $record=[ordered]@{path=$path;exists=$true;identity=$before}
    if ($file.Extension -in @('.exe','.dll')) {
        $version=[Diagnostics.FileVersionInfo]::GetVersionInfo($path)
        $record.version=[ordered]@{file_version=$version.FileVersion;product_version=$version.ProductVersion;product_name=$version.ProductName;company_name=$version.CompanyName;original_filename=$version.OriginalFilename;description=$version.FileDescription}
        $stream=[IO.File]::OpenRead($path)
        $reader=[IO.BinaryReader]::new($stream)
        try {
            if ($reader.ReadUInt16() -ne 0x5a4d) { throw 'Expected MZ image' }
            $stream.Position=0x3c
            $peOffset=$reader.ReadUInt32()
            if ($peOffset+6 -gt $stream.Length) { throw 'PE header outside file' }
            $stream.Position=$peOffset
            if ($reader.ReadUInt32() -ne 0x4550) { throw 'Expected PE signature' }
            $machine=$reader.ReadUInt16()
            $record.pe_machine=('0x{0:x4}' -f $machine)
            $record.pe_architecture=if ($machine -eq 0x14c) {'x86'} elseif ($machine -eq 0x8664) {'x64'} else {'other'}
        } finally { $reader.Dispose();$stream.Dispose() }
    }
    if ($file.Name -eq 'gameinfo.txt') {
        $text=Get-Content -LiteralPath $path -Raw -Encoding UTF8
        $record.relevant_configuration_lines=@($text -split "`r?`n" | Where-Object { $_ -match '^\s*(SteamAppId|ToolsAppId|Game\s|game\+|gamebin|mod\+|platform\s|"Engine"|"ToolsDir")' } | ForEach-Object { $_.Trim() })
    }
    if ($file.Name -eq 'run_hlmv_template.bat') {
        $record.installed_launch_template=(Get-Content -LiteralPath $path -Raw -Encoding UTF8).Trim()
    }
    $after=Get-Item -LiteralPath $path
    $record.unchanged_read=($after.Length -eq $before.bytes -and $after.LastWriteTimeUtc.ToString('o') -eq $before.mtime_utc -and (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -eq $before.sha256)
    if (-not $record.unchanged_read) { throw ('Installed file changed during read: '+$path) }
    $records+=$record
}
$modelHeaders=@()
foreach ($path in @((Join-Path $sfm 'tf\models\player\hwm\scout.mdl'),(Join-Path $sfm 'hl2\models\alyx.mdl'))) {
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        $file=Get-Item -LiteralPath $path
        $stream=[IO.File]::OpenRead($path);$reader=[IO.BinaryReader]::new($stream)
        try { $identifier=[Text.Encoding]::ASCII.GetString($reader.ReadBytes(4));$modelVersion=$reader.ReadInt32() } finally {$reader.Dispose();$stream.Dispose()}
        $modelHeaders+=[ordered]@{path=$path;bytes=$file.Length;mtime_utc=$file.LastWriteTimeUtc.ToString('o');identifier=$identifier;mdl_version=$modelVersion;read_scope='Only first eight header bytes; no geometry decoded. Shipped file is a compatibility lead, not proof this HLMV can load it.'}
    }
}
$result=[ordered]@{format='has_installed_native_source_viewer_inventory_1';created_utc=[DateTime]::UtcNow.ToString('o');scope='Explicit SFM/GMod viewer/compiler and material-system companion metadata only; no launch, extraction, install, Steam write or registry access.';records=$records;shipped_model_headers=$modelHeaders;viewer_load_render_capture='UNRUN';mdl49_viewer_compatibility='UNVERIFIED';steam_files_changed=$false}
[IO.File]::WriteAllText($output,($result|ConvertTo-Json -Depth 12)+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
[ordered]@{output=$output;sha256=(Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash.ToLowerInvariant();existing_files=@($records|Where-Object {$_.exists}).Count;viewers=@($records|Where-Object {$_.path -like '*\hlmv.exe'}|ForEach-Object {[ordered]@{path=$_.path;architecture=$_.pe_architecture;version=$_.version.file_version;sha256=$_.identity.sha256}});shipped_model_headers=$modelHeaders}|ConvertTo-Json -Depth 8 -Compress
