# GitHub API Script to Update File
$owner = "KillHosein"
$repo = "v2bot"
$branch = "main"
$filePath = "bot/app.py"
$commitMessage = "Fix: Add fallback handlers to ticket conversation

- Added support_menu, start_main, and cancel_flow as fallback handlers
- Fixes issue where users get stuck in SUPPORT_AWAIT_TICKET state
- Resolves ticket registration problem"

Write-Host "🔍 Reading local file..." -ForegroundColor Cyan
$localFile = Get-Content "bot\app.py" -Raw -Encoding UTF8
$contentBytes = [System.Text.Encoding]::UTF8.GetBytes($localFile)
$contentBase64 = [System.Convert]::ToBase64String($contentBytes)

Write-Host "📡 Getting current file SHA from GitHub..." -ForegroundColor Cyan
$apiUrl = "https://api.github.com/repos/$owner/$repo/contents/$filePath`?ref=$branch"

try {
    $response = Invoke-RestMethod -Uri $apiUrl -Method Get -Headers @{
        "Accept" = "application/vnd.github.v3+json"
        "User-Agent" = "PowerShell"
    }
    $currentSha = $response.sha
    Write-Host "✅ Current SHA: $currentSha" -ForegroundColor Green
} catch {
    Write-Host "❌ Error getting file info: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "📝 You'll need to authenticate. Please:" -ForegroundColor Yellow
    Write-Host "1. Go to https://github.com/KillHosein/v2bot/blob/main/bot/app.py" -ForegroundColor Yellow
    Write-Host "2. Click the pencil icon (Edit)" -ForegroundColor Yellow
    Write-Host "3. Replace lines 968-972 with:" -ForegroundColor Yellow
    Write-Host @"
        fallbacks=[
            CallbackQueryHandler(support_menu, pattern='^support_menu$'),
            CallbackQueryHandler(start_command, pattern='^start_main$'),
            CallbackQueryHandler(cancel_flow, pattern='^cancel_flow$'),
        ],
"@ -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "⚠️  GitHub API requires authentication for push operations." -ForegroundColor Yellow
Write-Host ""
Write-Host "Please use one of these methods:" -ForegroundColor Cyan
Write-Host ""
Write-Host "📌 Method 1: Direct GitHub Edit (Easiest)" -ForegroundColor Green
Write-Host "1. Go to: https://github.com/KillHosein/v2bot/edit/main/bot/app.py" -ForegroundColor White
Write-Host "2. Find line 968: fallbacks=[]," -ForegroundColor White
Write-Host "3. Replace with:" -ForegroundColor White
Write-Host @"
        fallbacks=[
            CallbackQueryHandler(support_menu, pattern='^support_menu$'),
            CallbackQueryHandler(start_command, pattern='^start_main$'),
            CallbackQueryHandler(cancel_flow, pattern='^cancel_flow$'),
        ],
"@ -ForegroundColor Cyan
Write-Host "4. Commit with message: Fix ticket registration issue" -ForegroundColor White
Write-Host ""
Write-Host "📌 Method 2: Install Git and Push" -ForegroundColor Green
Write-Host "Download from: https://git-scm.com/download/win" -ForegroundColor White
Write-Host ""

# Open the GitHub edit page
$editUrl = "https://github.com/$owner/$repo/edit/$branch/$filePath"
Write-Host "🌐 Opening GitHub edit page in browser..." -ForegroundColor Cyan
Start-Process $editUrl
