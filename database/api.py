from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .database import get_connection, init_db

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


app = FastAPI(
    title="Inventory & Cart API",
    description="Simple API for inventory, cart, and checkout operations",
    version="1.0.0",
)

# Allow the static frontend (served from any local origin) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database when application starts
init_db()

# Request Models
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)

class AddToCartRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

# Health Check
@app.get("/api/health")
def health():
    return {
        "message": "Inventory & Cart API is running"
    }

# PRODUCTS
# POST /api/products
@app.post("/api/products", status_code=201)
def create_product(product: ProductCreate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO products (name, price, stock)
        VALUES (?, ?, ?)
        """,
        (
            product.name,
            product.price,
            product.stock,
        )
    )

    product_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "message": "Product created successfully",
        "product_id": product_id,
    }


# GET /api/products
@app.get("/api/products")
def get_products():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, price, stock
        FROM products
        ORDER BY id
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]


# GET /api/products/{product_id}
@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, price, stock
        FROM products
        WHERE id = ?
        """,
        (product_id,)
    )

    product = cursor.fetchone()

    conn.close()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return dict(product)

# CART
# POST /api/cart
@app.post("/api/cart")
def add_to_cart(item: AddToCartRequest):
    conn = get_connection()
    cursor = conn.cursor()

    # Check if product exists

    cursor.execute(
        """
        SELECT id, name, price, stock
        FROM products
        WHERE id = ?
        """,
        (item.product_id,)
    )

    product = cursor.fetchone()

    if product is None:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Check requested quantity against stock

    if item.quantity > product["stock"]:
        conn.close()

        raise HTTPException(
            status_code=400,
            detail=f"Only {product['stock']} units available"
        )

    # Check if product already exists in cart

    cursor.execute(
        """
        SELECT id, quantity
        FROM inventory_items
        WHERE product_id = ?
        """,
        (item.product_id,)
    )

    existing = cursor.fetchone()

    if existing:
        new_quantity = existing["quantity"] + item.quantity

        # Make sure total cart quantity doesn't exceed stock
        if new_quantity > product["stock"]:
            conn.close()

            raise HTTPException(
                status_code=400,
                detail=f"Only {product['stock']} units available"
            )

        cursor.execute(
            """
            UPDATE inventory_items
            SET quantity = ?
            WHERE id = ?
            """,
            (
                new_quantity,
                existing["id"],
            )
        )

    else:
        cursor.execute(
            """
            INSERT INTO inventory_items (product_id, quantity)
            VALUES (?, ?)
            """,
            (
                item.product_id,
                item.quantity,
            )
        )

    conn.commit()
    conn.close()

    return {
        "message": "Item added to cart",
        "product_id": item.product_id,
        "quantity": item.quantity,
    }


# GET /api/cart
@app.get("/api/cart")
def get_cart():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            inventory_items.id,
            inventory_items.product_id,
            products.name,
            products.price,
            inventory_items.quantity,
            products.price * inventory_items.quantity AS total
        FROM inventory_items
        JOIN products
            ON inventory_items.product_id = products.id
        ORDER BY inventory_items.id
        """
    )

    rows = cursor.fetchall()

    conn.close()

    cart = [dict(row) for row in rows]

    # Calculate cart total
    cart_total = sum(item["total"] for item in cart)

    return {
        "items": cart,
        "cart_total": cart_total,
    }


# DELETE /api/cart/{product_id}
@app.delete("/api/cart/{product_id}")
def remove_from_cart(product_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM inventory_items
        WHERE product_id = ?
        """,
        (product_id,)
    )

    item = cursor.fetchone()

    if item is None:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Product not found in cart"
        )

    cursor.execute(
        """
        DELETE FROM inventory_items
        WHERE product_id = ?
        """,
        (product_id,)
    )

    conn.commit()
    conn.close()

    return {
        "message": "Item removed from cart",
        "product_id": product_id,
    }

# CHECKOUT
# POST /api/checkout
@app.post("/api/checkout")
def checkout():
    conn = get_connection()
    cursor = conn.cursor()

    # Check whether cart has items
    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM inventory_items
        """
    )

    result = cursor.fetchone()

    if result["count"] == 0:
        conn.close()

        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    # Clear cart
    cursor.execute(
        """
        DELETE FROM inventory_items
        """
    )

    conn.commit()
    conn.close()

    return {
        "message": "Checkout successful. Cart cleared."
    }

@app.delete("/api/delete")
def clear_cart():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE from inventory_items
        """
    )

    conn.commit()
    conn.close()

    return {"message": "Cart Cleared Successfully."}

# Serve the static frontend. Registered last so it never shadows the /api/*
# routes above — this mount is a catch-all for everything else.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")