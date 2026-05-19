param(
    [string]$BaseUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

$envPath = Join-Path $PSScriptRoot "..\.env"
if (-not (Test-Path $envPath)) {
    throw ".env file not found at $envPath"
}

$apiKey = (Get-Content $envPath | Where-Object { $_ -match '^APP_API_KEY=' } | Select-Object -First 1) -replace '^APP_API_KEY=', ''
if (-not $apiKey) {
    throw "APP_API_KEY not found in .env"
}

$headers = @{
    "x-api-key" = $apiKey
    "content-type" = "application/json"
}

function Invoke-ShoeApi {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Path,
        [object]$Body = $null
    )

    Write-Host "Testing $Name..." -ForegroundColor Cyan
    $params = @{
        Uri = "$BaseUrl$Path"
        Method = $Method
        Headers = $headers
        TimeoutSec = 30
    }
    if ($null -ne $Body) {
        $params.Body = ($Body | ConvertTo-Json -Depth 20)
    }
    return Invoke-RestMethod @params
}

$suffix = Get-Date -Format "yyyyMMddHHmmss"

$health = Invoke-RestMethod -Uri "$BaseUrl/" -Method Get
Write-Host "Health: $($health.status) - $($health.message)" -ForegroundColor Green

$productAnswer = Invoke-ShoeApi "business product answer" "GET" "/api/business/product-answer?model=RunnerX%20Pro&size=UK%209&color=Black"
Write-Host $productAnswer.answer -ForegroundColor Green

$inventoryBefore = Invoke-ShoeApi "inventory lookup" "GET" "/api/inventory/RUNX-BLK-09"
Write-Host "RUNX-BLK-09 available before reserve: $($inventoryBefore.inventory.available_quantity)" -ForegroundColor Green

$reserve = Invoke-ShoeApi "inventory reserve" "POST" "/api/inventory/reserve" @{
    sku = "RUNX-BLK-09"
    quantity = 1
}
Write-Host $reserve.message -ForegroundColor Green

$release = Invoke-ShoeApi "inventory release" "POST" "/api/inventory/release" @{
    sku = "RUNX-BLK-09"
    quantity = 1
}
Write-Host $release.message -ForegroundColor Green

$customer = Invoke-ShoeApi "create customer" "POST" "/api/customers" @{
    customer_name = "Test Maestro Customer $suffix"
    email = "maestro.$suffix@example.com"
    phone = "+9100$suffix"
    city = "Pune"
    source = "Smoke Test"
    assigned_sales_owner = "API Tester"
}
$customerId = $customer.customer.id
Write-Host "Customer created: $customerId" -ForegroundColor Green

Invoke-ShoeApi "patch customer status" "PATCH" "/api/customers/$customerId/status" @{
    current_stage = "Qualified Lead"
    latest_update = "Customer confirmed interest in RunnerX Pro."
    next_action = "Prepare quotation"
    priority = "High"
} | Out-Null

$quotation = Invoke-ShoeApi "create quotation" "POST" "/api/quotations" @{
    customer_id = $customerId
    quotation_number = "QT-$suffix"
    valid_until = "2026-06-30"
    created_by = "API Tester"
    items = @(
        @{ sku = "RUNX-BLK-09"; quantity = 2 },
        @{ sku = "STRF-BLU-07"; quantity = 1 }
    )
}
$quotationId = $quotation.quotation.id
Write-Host "Quotation created: $quotationId / $($quotation.quotation.quotation_number)" -ForegroundColor Green

Invoke-ShoeApi "send quotation" "POST" "/api/quotations/$quotationId/send" | Out-Null

$order = Invoke-ShoeApi "create order from quotation" "POST" "/api/orders/from-quotation" @{
    quotation_id = $quotationId
    order_number = "ORD-$suffix"
    delivery_city = "Pune"
}
$orderId = $order.order.id
Write-Host "Order created: $orderId / $($order.order.order_number)" -ForegroundColor Green

Invoke-ShoeApi "patch order status" "PATCH" "/api/orders/$orderId/status" @{
    payment_status = "Paid"
    fulfillment_status = "Packed"
    shipment_status = "Ready to Ship"
    latest_update = "Payment received and order packed."
} | Out-Null

$maestro = Invoke-ShoeApi "create Maestro process" "POST" "/api/maestro/processes" @{
    maestro_instance_id = "maestro-$suffix"
    customer_id = $customerId
    order_id = $orderId
    quotation_id = $quotationId
    current_step = "Waiting for Human Approval"
    process_status = "Waiting for Human Approval"
}
Write-Host "Maestro process created: $($maestro.process.maestro_instance_id)" -ForegroundColor Green

Invoke-ShoeApi "patch Maestro process" "PATCH" "/api/maestro/processes/maestro-$suffix" @{
    current_step = "Order Confirmed"
    process_status = "Completed"
    exception_flag = $false
} | Out-Null

$customerSummary = Invoke-ShoeApi "customer summary" "GET" "/api/business/customer-summary/$customerId"
$orderSummary = Invoke-ShoeApi "order summary" "GET" "/api/business/order-summary/$orderId"
$timeline = Invoke-ShoeApi "customer timeline" "GET" "/api/customers/$customerId/timeline"

Write-Host ""
Write-Host "Customer summary: $($customerSummary.answer)" -ForegroundColor Yellow
Write-Host "Order summary: $($orderSummary.answer)" -ForegroundColor Yellow
Write-Host "Timeline activities: $($timeline.activities.Count)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Smoke test completed successfully." -ForegroundColor Green
