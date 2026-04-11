#!/usr/bin/env pwsh
<#
.SYNOPSIS
Pre-deployment validation script for Socio AI platform
.DESCRIPTION
Validates backend, frontend, and deployment readiness before pushing to production
.EXAMPLE
./pre-deploy-check.ps1
#>

param(
    [switch]$SkipBackendTests,
    [switch]$SkipFrontendBuild
)

# Color helpers
$successColor = "Green"
$errorColor = "Red"
$warningColor = "Yellow"
$infoColor = "Cyan"

function Write-Success { Write-Host "[PASS] $args" -ForegroundColor $successColor }
function Write-Failure { Write-Host "[FAIL] $args" -ForegroundColor $errorColor }
function Write-Warning { Write-Host "[WARN] $args" -ForegroundColor $warningColor }
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor $infoColor }

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  SOCIO AI PRE-DEPLOYMENT VALIDATION" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date
$validationsPassed = 0
$validationsFailed = 0

Write-Host "Checking deployment tools..." -ForegroundColor Cyan

if ((railway --version 2>$null) -and (vercel --version 2>$null)) {
    Write-Success "Railway CLI: $(railway --version)"
    Write-Success "Vercel CLI: $(vercel --version)"
    $validationsPassed += 2
} else {
    Write-Failure "Missing CLI tools. Run: npm install -g @railway/cli vercel"
    $validationsFailed += 2
}

Write-Host ""
Write-Host "Checking CLI authentication..." -ForegroundColor Cyan

$vercelUser = vercel whoami 2>$null
if ($vercelUser) {
    Write-Success "Vercel CLI authenticated as: $vercelUser"
    $validationsPassed++
} else {
    Write-Failure "Vercel CLI not authenticated. Run: vercel login"
    $validationsFailed++
}

$railwayStatus = railway status 2>$null
if ($railwayStatus -and $railwayStatus -notmatch "Unauthorized") {
    Write-Success "Railway CLI authenticated"
    $validationsPassed++
} else {
    Write-Warning "Railway CLI not authenticated. You will need to run: railway login"
}

Write-Host ""
Write-Host "Building frontend..." -ForegroundColor Cyan

if (-not $SkipFrontendBuild) {
    Push-Location frontend
    $buildOutput = npm run build 2>&1
    Pop-Location
    
    if ($buildOutput -match "Compiled successfully") {
        Write-Success "Frontend compiled successfully"
        $validationsPassed++
    } else {
        Write-Failure "Frontend build failed!"
        Write-Host $buildOutput
        $validationsFailed++
    }
} else {
    Write-Info "Skipping frontend build"
}

Write-Host ""
Write-Host "Checking git status..." -ForegroundColor Cyan

$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Warning "Uncommitted changes detected - commit before deploying"
    Write-Host $gitStatus
    $validationsFailed++
} else {
    Write-Success "Git working directory clean"
    $validationsPassed++
}

$latestCommit = git rev-parse --short HEAD
Write-Info "Latest commit: $latestCommit"

Write-Host ""
Write-Host "Checking Dockerfile..." -ForegroundColor Cyan

if (Test-Path Dockerfile) {
    Write-Success "Dockerfile exists"
    $validationsPassed++
} else {
    Write-Failure "Dockerfile not found in project root"
    $validationsFailed++
}

Write-Host ""
$endTime = Get-Date
$elapsed = ($endTime - $startTime).TotalSeconds

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  VALIDATION SUMMARY" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "  Passed:  $validationsPassed" -ForegroundColor Green
Write-Host "  Failed:  $validationsFailed" -ForegroundColor $(if ($validationsFailed -eq 0) { "Green" } else { "Red" })
Write-Host "  Time:    ${elapsed}s" -ForegroundColor Cyan
Write-Host ""

if ($validationsFailed -eq 0) {
    Write-Host "SUCCESS - All validations passed! Ready to deploy." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Read: DEPLOY_INTERACTIVE.md" -ForegroundColor Cyan
    Write-Host "  2. Run: railway login (one-time)" -ForegroundColor Cyan
    Write-Host "  3. Run: railway link (one-time)" -ForegroundColor Cyan
    Write-Host "  4. Deploy: git push origin main" -ForegroundColor Cyan
    Write-Host ""
    exit 0
} else {
    Write-Host "FAILED - Please fix issues above" -ForegroundColor Red
    Write-Host ""
    exit 1
}
