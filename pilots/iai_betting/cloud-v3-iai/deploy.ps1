<#
.SYNOPSIS
    Deploy IAI Betting Tracker to Azure
.DESCRIPTION
    Creates all Azure resources and deploys the function app.
    Run this script once to set everything up.
.PARAMETER ResourceGroupName
    Name for the Azure resource group (default: iai-betting-rg)
.PARAMETER Location
    Azure region (default: uksouth)
.PARAMETER StorageAccountName
    Name for storage account - must be globally unique (default: iaibetting + random suffix)
.PARAMETER FunctionAppName
    Name for function app - must be globally unique (default: iai-betting-tracker + random suffix)
#>

param(
    [string]$ResourceGroupName = "iai-betting-rg",
    [string]$Location = "uksouth",
    [string]$StorageAccountName = "",
    [string]$FunctionAppName = ""
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        IAI BETTING TRACKER - AZURE DEPLOYMENT                ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Generate unique names if not provided
$suffix = Get-Random -Minimum 1000 -Maximum 9999
if (-not $StorageAccountName) {
    $StorageAccountName = "iaibetting$suffix"
}
if (-not $FunctionAppName) {
    $FunctionAppName = "iai-betting-$suffix"
}

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Resource Group:   $ResourceGroupName"
Write-Host "  Location:         $Location"
Write-Host "  Storage Account:  $StorageAccountName"
Write-Host "  Function App:     $FunctionAppName"
Write-Host ""

# Check if Azure CLI is installed
Write-Host "Checking Azure CLI..." -ForegroundColor Yellow
try {
    $azVersion = az version 2>$null | ConvertFrom-Json
    Write-Host "  ✓ Azure CLI installed (v$($azVersion.'azure-cli'))" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Azure CLI not found. Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Red
    exit 1
}

# Check if Azure Functions Core Tools is installed
Write-Host "Checking Azure Functions Core Tools..." -ForegroundColor Yellow
try {
    $funcVersion = func --version 2>$null
    Write-Host "  ✓ Functions Core Tools installed (v$funcVersion)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Azure Functions Core Tools not found." -ForegroundColor Red
    Write-Host "    Install with: npm install -g azure-functions-core-tools@4" -ForegroundColor Yellow
    exit 1
}

# Login check
Write-Host "Checking Azure login..." -ForegroundColor Yellow
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "  → Logging in to Azure..." -ForegroundColor Yellow
    az login
    $account = az account show | ConvertFrom-Json
}
Write-Host "  ✓ Logged in as: $($account.user.name)" -ForegroundColor Green
Write-Host "  ✓ Subscription: $($account.name)" -ForegroundColor Green
Write-Host ""

# Confirm before proceeding
Write-Host "This will create Azure resources (estimated cost: <£1/month)" -ForegroundColor Yellow
$confirm = Read-Host "Continue? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "Cancelled." -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "Step 1: Creating Resource Group..." -ForegroundColor Cyan
az group create --name $ResourceGroupName --location $Location --output none
Write-Host "  ✓ Resource group created" -ForegroundColor Green

Write-Host ""
Write-Host "Step 2: Creating Storage Account..." -ForegroundColor Cyan
az storage account create `
    --name $StorageAccountName `
    --resource-group $ResourceGroupName `
    --location $Location `
    --sku Standard_LRS `
    --output none
Write-Host "  ✓ Storage account created" -ForegroundColor Green

Write-Host ""
Write-Host "Step 3: Getting Connection String..." -ForegroundColor Cyan
$connectionString = az storage account show-connection-string `
    --name $StorageAccountName `
    --resource-group $ResourceGroupName `
    --query connectionString -o tsv
Write-Host "  ✓ Connection string retrieved" -ForegroundColor Green

Write-Host ""
Write-Host "Step 4: Creating Function App..." -ForegroundColor Cyan
az functionapp create `
    --name $FunctionAppName `
    --resource-group $ResourceGroupName `
    --storage-account $StorageAccountName `
    --consumption-plan-location $Location `
    --runtime python `
    --runtime-version 3.11 `
    --functions-version 4 `
    --os-type linux `
    --output none
Write-Host "  ✓ Function app created" -ForegroundColor Green

Write-Host ""
Write-Host "Step 5: Configuring App Settings..." -ForegroundColor Cyan
az functionapp config appsettings set `
    --name $FunctionAppName `
    --resource-group $ResourceGroupName `
    --settings "AZURE_STORAGE_CONNECTION_STRING=$connectionString" `
    --output none
Write-Host "  ✓ Settings configured" -ForegroundColor Green

Write-Host ""
Write-Host "Step 6: Deploying Functions..." -ForegroundColor Cyan
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir
try {
    func azure functionapp publish $FunctionAppName --python
    Write-Host "  ✓ Functions deployed" -ForegroundColor Green
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    DEPLOYMENT COMPLETE!                      ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Your endpoints:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Dashboard (HTML):" -ForegroundColor Cyan
Write-Host "    https://$FunctionAppName.azurewebsites.net/api/dashboard?format=html"
Write-Host ""
Write-Host "  Dashboard (JSON):" -ForegroundColor Cyan
Write-Host "    https://$FunctionAppName.azurewebsites.net/api/dashboard"
Write-Host ""
Write-Host "  Manual Run (POST):" -ForegroundColor Cyan
Write-Host "    https://$FunctionAppName.azurewebsites.net/api/run_now"
Write-Host ""
Write-Host "The tracker runs automatically every day at 18:00 UTC." -ForegroundColor Yellow
Write-Host ""

# Trigger first run
Write-Host "Triggering first run..." -ForegroundColor Cyan
try {
    $result = Invoke-RestMethod -Uri "https://$FunctionAppName.azurewebsites.net/api/run_now" -Method POST
    Write-Host "  ✓ First run completed" -ForegroundColor Green
    Write-Host "    Bankroll: £$($result.bankroll)" -ForegroundColor White
} catch {
    Write-Host "  ⚠ First run failed (may need a minute to warm up)" -ForegroundColor Yellow
}

# Open dashboard
Write-Host ""
$openDashboard = Read-Host "Open dashboard in browser? (y/n)"
if ($openDashboard -eq 'y') {
    Start-Process "https://$FunctionAppName.azurewebsites.net/api/dashboard?format=html"
}

Write-Host ""
Write-Host "Done! Your betting tracker is now running in the cloud." -ForegroundColor Green
