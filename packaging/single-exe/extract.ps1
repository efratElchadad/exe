$ErrorActionPreference = 'Stop'
$dest = $env:AC_PACKAGE_DEST
$expected = $env:AC_PACKAGE_SHA
$source = $env:AC_PACKAGE_SELF
$parent = [IO.Path]::GetDirectoryName($dest)
[IO.Directory]::CreateDirectory($parent) | Out-Null
$mutex = New-Object Threading.Mutex($false, ('Local\AndroidCompiler-' + $expected.Substring(0,20)))
$locked = $false
$stage = $null
try {
    try { $locked = $mutex.WaitOne(120000) } catch [Threading.AbandonedMutexException] { $locked = $true }
    if (-not $locked) { throw 'Another extraction did not finish in time.' }
    $marker = Join-Path $dest 'package.sha256'
    $ready = (Test-Path -LiteralPath $marker) -and ((Get-Content -LiteralPath $marker -Raw).Trim() -eq $expected)
    $ready = $ready -and (Test-Path -LiteralPath (Join-Path $dest 'AndroidCompiler\AndroidCompiler.exe'))
    $ready = $ready -and (Test-Path -LiteralPath (Join-Path $dest 'AndroidCompiler\runtime\pythonw.exe'))
    $ready = $ready -and (Test-Path -LiteralPath (Join-Path $dest 'AndroidCompiler\app\bootstrap.py'))
    if (-not $ready) {
        $stage = Join-Path $parent ([Guid]::NewGuid().ToString('N'))
        [IO.Directory]::CreateDirectory($stage) | Out-Null
        $archive = Join-Path $stage 'payload.zip'
        $packageStream = [IO.File]::OpenRead($source)
        try {
            $reader = New-Object IO.BinaryReader($packageStream)
            $packageStream.Seek(-16, [IO.SeekOrigin]::End) | Out-Null
            $magic = [Text.Encoding]::ASCII.GetString($reader.ReadBytes(8))
            $length = $reader.ReadInt64()
            if ($magic -ne 'ACEXE001' -or $length -le 0 -or $length -gt ($packageStream.Length - 16)) { throw 'Invalid application package.' }
            $packageStream.Seek(-16 - $length, [IO.SeekOrigin]::End) | Out-Null
            $output = [IO.File]::Create($archive)
            try {
                $buffer = New-Object byte[] 1048576
                $left = $length
                while ($left -gt 0) {
                    $read = $packageStream.Read($buffer, 0, [int][Math]::Min($buffer.Length, $left))
                    if ($read -le 0) { throw 'Incomplete application package.' }
                    $output.Write($buffer, 0, $read)
                    $left -= $read
                }
            } finally { $output.Dispose() }
        } finally { $packageStream.Dispose() }
        $sha = [Security.Cryptography.SHA256]::Create()
        $stream = [IO.File]::OpenRead($archive)
        try { $actual = ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
        finally { $stream.Dispose(); $sha.Dispose() }
        if ($actual -ne $expected) { throw 'Application integrity check failed. Download the EXE again.' }
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $unpacked = Join-Path $stage 'unpacked'
        [IO.Compression.ZipFile]::ExtractToDirectory($archive, $unpacked)
        if (-not (Test-Path -LiteralPath (Join-Path $unpacked 'AndroidCompiler\runtime\pythonw.exe'))) { throw 'Runtime is missing.' }
        [IO.File]::WriteAllText((Join-Path $unpacked 'package.sha256'), $expected)
        if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Recurse -Force }
        [IO.Directory]::Move($unpacked, $dest)
    }
} catch {
    $_.Exception.ToString() | Out-File -LiteralPath (Join-Path $parent 'extraction-error.log') -Encoding utf8
    exit 1
} finally {
    if ($stage -and (Test-Path -LiteralPath $stage)) { Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue }
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
exit 0
