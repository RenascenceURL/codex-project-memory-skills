param(
    [string]$SkillRoot = "$HOME\\.codex\\skills\\project-memory-rules",
    [switch]$NoCodexWrap,
    [switch]$CurrentHostOnly
)

$ErrorActionPreference = "Stop"

$memoryScript = Join-Path $SkillRoot "scripts\\memory_manager.py"
if (-not (Test-Path $memoryScript)) {
    throw "memory_manager.py not found at: $memoryScript"
}

$profilePath = if ($CurrentHostOnly) { $PROFILE.CurrentUserCurrentHost } else { $PROFILE.CurrentUserAllHosts }
$profileDir = Split-Path -Parent $profilePath
if (-not (Test-Path $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}

$startMarker = "# >>> project-memory-rules >>>"
$endMarker = "# <<< project-memory-rules <<<"
$memoryScriptLiteral = $memoryScript.Replace("'", "''")

$codexWrapBlock = @'
$script:ProjectMemoryRulesRealCodex = $null
$knownCodexSubcommands = @('exec','review','login','logout','mcp','mcp-server','app-server','completion','sandbox','debug','apply','resume','fork','cloud','features','help')
$realCodex = Get-Command codex -CommandType Application,ExternalScript -ErrorAction SilentlyContinue | Select-Object -First 1
if ($realCodex) {
    $script:ProjectMemoryRulesRealCodex = $realCodex.Source
    function codex {
        param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)

        $projectPath = (Get-Location).Path
        $ctx = Invoke-ProjectMemoryContext -ProjectPath $projectPath
        $shouldInject = $false

        if ($ctx -and $ctx.prompt_payload) {
            if ($Args.Count -eq 0) {
                $shouldInject = $true
            } else {
                $first = $Args[0].ToLower()
                if ((-not $first.StartsWith('-')) -and (-not ($knownCodexSubcommands -contains $first))) {
                    $shouldInject = $true
                }
            }
        }

        if (-not $script:ProjectMemoryRulesRealCodex) {
            Write-Error "Real codex binary not found."
            return
        }

        if ($shouldInject) {
            if ($Args.Count -eq 0) {
                & $script:ProjectMemoryRulesRealCodex $ctx.prompt_payload
            } else {
                $userPrompt = $Args -join ' '
                $mergedPrompt = "$($ctx.prompt_payload)`n`n[USER REQUEST]`n$userPrompt"
                & $script:ProjectMemoryRulesRealCodex $mergedPrompt
            }
            return
        }

        & $script:ProjectMemoryRulesRealCodex @Args
    }
}
'@

if ($NoCodexWrap) {
    $codexWrapBlock = "# codex wrap disabled by -NoCodexWrap"
}

$snippet = @'
__START_MARKER__
$global:ProjectMemoryRulesScript = '__MEMORY_SCRIPT__'

function Invoke-ProjectMemoryContext {
    param(
        [string]$ProjectPath = (Get-Location).Path,
        [switch]$Quiet
    )

    if (-not (Test-Path $global:ProjectMemoryRulesScript)) {
        Write-Error "memory_manager.py not found: $global:ProjectMemoryRulesScript"
        return $null
    }

    $raw = & python $global:ProjectMemoryRulesScript context --project-path $ProjectPath --json
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($raw)) {
        return $null
    }

    try {
        $ctx = $raw | ConvertFrom-Json
    } catch {
        Write-Error "Failed to parse context JSON."
        return $null
    }

    if (-not $Quiet -and $ctx.terminal_summary) {
        $ctx.terminal_summary | Out-Host
    }
    return $ctx
}

function /mem {
    param(
        [Parameter(Position = 0)][string]$Cmd,
        [string]$ProjectPath = (Get-Location).Path,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$Extra
    )

    if (-not (Test-Path $global:ProjectMemoryRulesScript)) {
        Write-Error "memory_manager.py not found: $global:ProjectMemoryRulesScript"
        return
    }

    if ([string]::IsNullOrWhiteSpace($Cmd)) {
        & python $global:ProjectMemoryRulesScript menu --project-path $ProjectPath
        return
    }

    $normalized = $Cmd.Trim().ToLower()

    if ($normalized -in @('1','/load','load')) {
        & python $global:ProjectMemoryRulesScript context --project-path $ProjectPath --print-summary
        return
    }

    if ($normalized -in @('3','/pick','pick')) {
        $tasksRaw = & python $global:ProjectMemoryRulesScript list-tasks --project-path $ProjectPath --json
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($tasksRaw)) {
            return
        }
        $tasks = $tasksRaw | ConvertFrom-Json
        if (-not $tasks -or $tasks.Count -eq 0) {
            Write-Host "No tasks found."
            return
        }
        for ($i = 0; $i -lt $tasks.Count; $i++) {
            $t = $tasks[$i]
            Write-Host ("{0}. {1} | {2} | {3} | {4}" -f ($i + 1), $t.task_id, $t.status, $t.updated, $t.title)
        }
        $sel = Read-Host "Select task number"
        $parsed = 0
        if (-not [int]::TryParse($sel, [ref]$parsed)) {
            Write-Host "Invalid selection."
            return
        }
        $idx = $parsed - 1
        if ($idx -lt 0 -or $idx -ge $tasks.Count) {
            Write-Host "Out of range."
            return
        }
        & python $global:ProjectMemoryRulesScript activate-task --project-path $ProjectPath --task-id $tasks[$idx].task_id
        return
    }

    if ($normalized -in @('2','4','/save','save','/advanced','advanced')) {
        & python $global:ProjectMemoryRulesScript menu --project-path $ProjectPath
        return
    }

    & python $global:ProjectMemoryRulesScript slash $Cmd --project-path $ProjectPath @Extra
}

Set-Alias /men /mem -Scope Global
Set-Alias /mr /mem -Scope Global

__CODEX_WRAP__
__END_MARKER__
'@

$snippet = $snippet.Replace("__START_MARKER__", $startMarker)
$snippet = $snippet.Replace("__END_MARKER__", $endMarker)
$snippet = $snippet.Replace("__MEMORY_SCRIPT__", $memoryScriptLiteral)
$snippet = $snippet.Replace("__CODEX_WRAP__", $codexWrapBlock)

$existing = ""
if (Test-Path $profilePath) {
    $existing = Get-Content -Path $profilePath -Raw
}

$pattern = "(?s)$([regex]::Escape($startMarker)).*?$([regex]::Escape($endMarker))"
$cleaned = [regex]::Replace($existing, $pattern, "").TrimEnd()
$newContent = if ([string]::IsNullOrWhiteSpace($cleaned)) { $snippet } else { "$cleaned`r`n`r`n$snippet" }
Set-Content -Path $profilePath -Value $newContent -Encoding utf8

Write-Host "Installed hooks into: $profilePath"
Write-Host "Run '. $profilePath' or restart PowerShell to apply."
Write-Host "Primary command: /mem"
Write-Host "Menu: /mem"
Write-Host "Quick read: /mem 1"
Write-Host "Manual pick: /mem 3"
if (-not $NoCodexWrap) {
    Write-Host "codex wrapper enabled: startup context is printed and injected into initial prompt."
}
