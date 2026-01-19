# Deployment Guide - Azure Functions

## Prerequisites

1. **Azure CLI** installed
2. **Azure Functions Core Tools** installed
3. An Azure subscription

## Step 1: Create Azure Resources

```powershell
# Login to Azure
az login

# Create resource group
az group create --name iai-betting-rg --location uksouth

# Create storage account (name must be globally unique)
az storage account create `
    --name iaibettingstorage `
    --resource-group iai-betting-rg `
    --location uksouth `
    --sku Standard_LRS

# Get storage connection string
$connectionString = az storage account show-connection-string `
    --name iaibettingstorage `
    --resource-group iai-betting-rg `
    --query connectionString -o tsv

# Create Function App
az functionapp create `
    --name iai-betting-tracker `
    --resource-group iai-betting-rg `
    --storage-account iaibettingstorage `
    --consumption-plan-location uksouth `
    --runtime python `
    --runtime-version 3.11 `
    --functions-version 4 `
    --os-type linux

# Set the storage connection string
az functionapp config appsettings set `
    --name iai-betting-tracker `
    --resource-group iai-betting-rg `
    --settings "AZURE_STORAGE_CONNECTION_STRING=$connectionString"
```

## Step 2: Deploy the Functions

```powershell
# Navigate to the cloud folder
cd pilots/iai_betting/cloud

# Deploy (first time may take a few minutes)
func azure functionapp publish iai-betting-tracker
```

## Step 3: Verify Deployment

After deployment, you'll have these endpoints:

- **Dashboard**: `https://iai-betting-tracker.azurewebsites.net/api/dashboard`
- **Dashboard HTML**: `https://iai-betting-tracker.azurewebsites.net/api/dashboard?format=html`
- **Manual Run**: `POST https://iai-betting-tracker.azurewebsites.net/api/run_now`

The timer function runs automatically at 18:00 UTC daily.

## Step 4: Test It

```powershell
# Trigger a manual run
Invoke-RestMethod -Uri "https://iai-betting-tracker.azurewebsites.net/api/run_now" -Method POST

# View dashboard
Start-Process "https://iai-betting-tracker.azurewebsites.net/api/dashboard?format=html"
```

## Monitoring

View logs in Azure Portal:
1. Go to your Function App
2. Click "Functions" in the left menu
3. Select a function
4. Click "Monitor" to see invocation logs

## Costs

With Azure Functions Consumption plan:
- **First 1 million executions free** per month
- Blob storage: ~$0.02/GB/month
- Total expected: **< $1/month**

## Local Development

```powershell
# Create local settings file
cp local.settings.json.template local.settings.json

# Edit local.settings.json and add your connection string

# Run locally
func start
```

## Updating the Strategy

Edit [shared/storage.py](shared/storage.py) to change:
- `odds_min` / `odds_max` - Odds range
- `stake_pct` - Stake percentage
- Initial bankroll

Then redeploy: `func azure functionapp publish iai-betting-tracker`
