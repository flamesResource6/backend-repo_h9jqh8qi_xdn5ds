import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from database import db, create_document, get_documents
from schemas import Product, Order

app = FastAPI(title="HNG PACKAGING SOLUTION API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "HNG PACKAGING SOLUTION backend is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Default catalog fallback when DB is not available or empty
DEFAULT_CATALOG: List[Product] = [
    Product(title="Corrugated Boxes (Set of 25)", description="Durable shipping cartons in multiple sizes.", price=49.99, category="Boxes", in_stock=True, image=None),
    Product(title="Kraft Paper Bags (100 pcs)", description="Eco-friendly retail carry bags.", price=34.50, category="Bags", in_stock=True, image=None),
    Product(title="Packaging Tape (6 rolls)", description="High-adhesion tape for secure sealing.", price=14.99, category="Tape", in_stock=True, image=None),
    Product(title="Bubble Wrap (100m)", description="Cushioning for fragile items.", price=24.99, category="Protective", in_stock=True, image=None),
]

# ---------------------------
# Products Endpoints
# ---------------------------
@app.get("/api/products", response_model=List[Product])
def list_products():
    # Try DB first
    try:
        docs = get_documents("product")
        items = []
        for doc in docs:
            items.append(Product(
                title=doc.get("title"),
                description=doc.get("description"),
                price=float(doc.get("price", 0)),
                category=doc.get("category"),
                in_stock=bool(doc.get("in_stock", True)),
                image=doc.get("image")
            ))
        # Fallback to default catalog if DB has no products
        if not items:
            return DEFAULT_CATALOG
        return items
    except Exception:
        # If DB not configured, return default catalog
        return DEFAULT_CATALOG

@app.post("/api/products", status_code=201)
def create_product(product: Product):
    try:
        inserted_id = create_document("product", product)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------
# Orders Endpoints
# ---------------------------
@app.post("/api/orders")
def create_order(order: Order):
    try:
        inserted_id = create_document("order", order)
        return {"id": inserted_id, "message": "Order placed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
