from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import business, customers, inventory, maestro, orders, products, quotations

app = FastAPI(
    title="Shoe Brand Order Management Backend",
    version="0.1.0",
    description="MVP backend for shoe brand order management and UiPath Maestro orchestration.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "Shoe Brand Order Management Backend is running",
    }


app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(customers.router)
app.include_router(quotations.router)
app.include_router(orders.router)
app.include_router(maestro.router)
app.include_router(business.router)
