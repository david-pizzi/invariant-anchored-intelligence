<#
.SYNOPSIS
    Deploy IAI Betting Tracker V3 to Azure
.DESCRIPTION
    Deploys IAI-enhanced betting tracker to a NEW function app.
    Does NOT touch existing iai-betting-tracker (v2).
#>

param(
    [string]$ResourceGroup = "IAI",
    [string]$FunctionAppName = "iai-betting-tracker-v3",
    [string]$StorageAccountName = "iaibettingstorage745"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "     IAI BETTING TRACKER V3 - SAFE DEPLOYMENT                 " -ForegroundColor Cyan
Write-Host "     (Existing v2 will continue running)                      " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Verify we're in the right directory
if (-not (Test-Path "shared/iai_core")) {
    Write-Host "ERROR: Run this from cloud-v3-iai directory!" -ForegroundColor Red
    Write-Host "Missing shared/iai_core - IAI modules not found" -ForegroundColor Red
    exit 1
}

Write-Host "OK IAI modules found in shared/iai_core" -ForegroundColor Green

# Check if logged in to Azure
Write-Host "`nChecking Azure login..." -ForegroundColor Yellow
try {
    $account = az account show 2>$null | ConvertFrom-Json
    Write-Host "OK Logged in as: $($account.user.name)" -ForegroundColor Green
}
catch {
    Write-Host "ERROR: Not logged in to Azure" -ForegroundColor Red
    Write-Host "Run: az login" -ForegroundColor Yellow
    exit 1
}

# Check if v3 function app already exists
Write-Host "`nChecking if $FunctionAppName exists..." -ForegroundColor Yellow
$ErrorActionPreference = "SilentlyContinue"
$existingApp = az functionapp show --name $FunctionAppName --resource-group $ResourceGroup 2>$null
$appExists = $LASTEXITCODE -eq 0
$ErrorActionPreference = "Stop"

if ($appExists) {
    Write-Host "OK Function app exists - will update" -ForegroundColor Yellow
}
else {
    Write-Host "Creating NEW function app: $FunctionAppName" -ForegroundColor Cyan
    
    # Create function app
    Write-Host "Creating Linux Python function app..." -ForegroundColor Yellow
    az functionapp create `
        --resource-group $ResourceGroup `
        --name $FunctionAppName `
        --storage-account $StorageAccountName `
        --consumption-plan-location uksouth `
        --runtime python `
        --runtime-version 3.11 `
        --functions-version 4 `
        --os-type Linux
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create function app" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "OK Function app created" -ForegroundColor Green
    
    # Configure app settings
    Write-Host "`nConfiguring app settings..." -ForegroundColor Yellow
    
    # Get storage connection string
    $storageConn = az storage account show-connection-string `
        --name $StorageAccountName `
        --resource-group $ResourceGroup `
        --query connectionString -o tsv
    
    # Set all required settings
    az functionapp config appsettings set `
        --name $FunctionAppName `
        --resource-group $ResourceGroup `
        --settings `
        "AZURE_STORAGE_CONNECTION_STRING=$storageConn" `
        "ODDS_API_KEY=27e87733ca9b5e5022d6ead4aebb3b55" `
        "ENABLE_IAI=true" `
        "IAI_EVALUATION_INTERVAL_DAYS=7"
    
    Write-Host "OK App settings configured" -ForegroundColor Green
}

# Deploy using Azure Functions Core Tools
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "DEPLOYING TO AZURE" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Function App: $FunctionAppName" -ForegroundColor Yellow
Write-Host "Resource Group: $ResourceGroup" -ForegroundColor Yellow
Write-Host ""

Write-Host "Running: func azure functionapp publish $FunctionAppName --python" -ForegroundColor Cyan
Write-Host ""

func azure functionapp publish $FunctionAppName --python

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nERROR: DEPLOYMENT FAILED!" -ForegroundColor Red
    Write-Host "Your existing v2 app is still running and unaffected." -ForegroundColor Green
    exit 1
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "                  DEPLOYMENT SUCCESSFUL!                        " -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""

Write-Host "IAI V3 Endpoints:" -ForegroundColor Cyan
Write-Host "  Dashboard: https://$FunctionAppName.azurewebsites.net/api/dashboard" -ForegroundColor White
Write-Host "  Run Now:   https://$FunctionAppName.azurewebsites.net/api/run_now" -ForegroundColor White
Write-Host ""

Write-Host "Old V2 Endpoints (still running):" -ForegroundColor Yellow
Write-Host "  Dashboard: https://iai-betting-tracker.azurewebsites.net/api/dashboard" -ForegroundColor White
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Test V3: Invoke-WebRequest https://$FunctionAppName.azurewebsites.net/api/dashboard" -ForegroundColor White
Write-Host "  2. Monitor both for 1 week" -ForegroundColor White
Write-Host "  3. If V3 works well, switch production traffic" -ForegroundColor White
Write-Host "  4. Keep V2 as backup for easy rollback" -ForegroundColor White
Write-Host ""
