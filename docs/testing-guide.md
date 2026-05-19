# Testing Guide

Your server is running if this works:

```powershell
Invoke-RestMethod http://localhost:8000/
```

Protected routes require:

```text
x-api-key: value_from_APP_API_KEY
```

## Current Blocker

If protected endpoints return `500 Internal Server Error` and Supabase reports:

```text
Could not find the table 'public.products' in the schema cache
```

then the Supabase SQL has not been executed in the project configured by `SUPABASE_URL`.

Run these files in Supabase SQL Editor:

1. `sql/schema.sql`
2. `sql/seed.sql`

Then wait a few seconds for PostgREST schema cache to refresh and test again.

## Automated Smoke Test

After the SQL files are executed and the local server is running:

```powershell
cd "C:\Agentic Orchestration\shoe-brand-backend"
.\scripts\smoke_test.ps1
```

The script will add fresh data to Supabase through your API:

- one customer
- one customer status update
- one quotation with two items
- one sent quotation event
- one order from the quotation
- one order status update
- one Maestro process
- inventory reserve and release checks

## Manual API Tests

Set your key for the current PowerShell session:

```powershell
$apiKey = (Get-Content .env | Where-Object { $_ -match '^APP_API_KEY=' }) -replace '^APP_API_KEY=', ''
$headers = @{ "x-api-key" = $apiKey; "content-type" = "application/json" }
```

Product availability and price:

```powershell
Invoke-RestMethod "http://localhost:8000/api/business/product-answer?model=RunnerX%20Pro&size=UK%209&color=Black" -Headers $headers
```

All available stock:

```powershell
Invoke-RestMethod "http://localhost:8000/api/inventory?available_only=true" -Headers $headers
```

All stock, including out-of-stock items:

```powershell
Invoke-RestMethod "http://localhost:8000/api/inventory?available_only=false" -Headers $headers
```

Low stock only:

```powershell
Invoke-RestMethod "http://localhost:8000/api/inventory?status=Low%20Stock" -Headers $headers
```

Inventory lookup:

```powershell
Invoke-RestMethod "http://localhost:8000/api/inventory/RUNX-BLK-09" -Headers $headers
```

Update exact stock quantity for one SKU:

```powershell
Invoke-RestMethod "http://localhost:8000/api/inventory/RUNX-BLK-09" -Method Patch -Headers $headers -Body '{"available_quantity":50}'
```

You can also update multiple stock fields:

```powershell
Invoke-RestMethod "http://localhost:8000/api/inventory/RUNX-BLK-09" -Method Patch -Headers $headers -Body '{"available_quantity":50,"reserved_quantity":0,"reorder_level":10}'
```

## Postman Stock Requests

Create a `GET` request with this URL:

```text
http://localhost:8000/api/inventory?available_only=true
```

Add this header:

```text
x-api-key: your_APP_API_KEY_value
```

Useful Postman URLs:

```text
GET http://localhost:8000/api/inventory?available_only=false
GET http://localhost:8000/api/inventory?status=Low%20Stock
GET http://localhost:8000/api/inventory/RUNX-BLK-09
PATCH http://localhost:8000/api/inventory/RUNX-BLK-09
```

For the `PATCH` request, use Body -> raw -> JSON:

```json
{
  "available_quantity": 50,
  "reserved_quantity": 0,
  "reorder_level": 10
}
```

Reserve inventory:

```powershell
Invoke-RestMethod "http://localhost:8000/api/inventory/reserve" -Method Post -Headers $headers -Body '{"sku":"RUNX-BLK-09","quantity":1}'
```

Release inventory:

```powershell
Invoke-RestMethod "http://localhost:8000/api/inventory/release" -Method Post -Headers $headers -Body '{"sku":"RUNX-BLK-09","quantity":1}'
```

Create customer:

```powershell
Invoke-RestMethod "http://localhost:8000/api/customers" -Method Post -Headers $headers -Body '{"customer_name":"Aarav Test","email":"aarav.test@example.com","phone":"+919900001111","city":"Pune","source":"Manual Test"}'
```

List all customers with status, latest activity, quotation, order, and Maestro process:

```powershell
Invoke-RestMethod "http://localhost:8000/api/customers" -Headers $headers
```

Filter customer list by operational fields:

```powershell
Invoke-RestMethod "http://localhost:8000/api/customers?stage=Quotation%20Sent" -Headers $headers
Invoke-RestMethod "http://localhost:8000/api/customers?priority=High" -Headers $headers
Invoke-RestMethod "http://localhost:8000/api/customers?quotation_requested=true" -Headers $headers
Invoke-RestMethod "http://localhost:8000/api/customers?owner=Anika%20Rao" -Headers $headers
```

## Postman Customer Requests

Create a `GET` request with this URL:

```text
http://localhost:8000/api/customers
```

Add this header:

```text
x-api-key: your_APP_API_KEY_value
```

Useful Postman URLs:

```text
GET http://localhost:8000/api/customers?stage=Quotation%20Sent
GET http://localhost:8000/api/customers?priority=High
GET http://localhost:8000/api/customers?quotation_requested=true
GET http://localhost:8000/api/customers?quotation_sent=true
GET http://localhost:8000/api/customers?city=Mumbai
GET http://localhost:8000/api/customers?owner=Anika%20Rao
```

Create Maestro process:

```powershell
Invoke-RestMethod "http://localhost:8000/api/maestro/processes" -Method Post -Headers $headers -Body '{"maestro_instance_id":"manual-maestro-001","current_step":"Check Inventory","process_status":"Running"}'
```

Open Swagger UI for interactive testing:

```text
http://localhost:8000/docs
```

Click `Authorize` is not configured for this custom header, so add `x-api-key` manually in each protected request from the Swagger endpoint's parameters if shown, or use PowerShell/curl for easier testing.
