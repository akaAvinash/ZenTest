# ZenTest — Inventory & Cart

A small FastAPI backend (products, cart, checkout) backed by SQLite, with a
plain HTML/CSS/JS frontend on top of it. No frameworks or build step —
just a REST API and a static page that talks to it.

## Project structure

```
database/
  api.py         FastAPI app: product, cart, and checkout endpoints
  database.py    SQLite connection + schema (creates inventory.db on first run)
frontend/
  index.html     Page layout
  style.css      Styling
  app.js         Talks to the API (fetch), renders products & cart
requirements.txt
```

## Running the backend

```bash
pip install -r requirements.txt
python -m uvicorn database.api:app --reload --port 8000
```

This creates `inventory.db` in the working directory on first run (it's
gitignored — each environment gets its own local database). The API docs
are available at `http://127.0.0.1:8000/docs`.

## Running the frontend

The frontend is static, so any local file server works:

```bash
cd frontend
python -m http.server 5500
```

Then open `http://127.0.0.1:5500` in a browser. The page calls the API at
`http://<same-host>:8000` (CORS is enabled on the backend for local dev), so
keep the backend running on port 8000 alongside it.

## API endpoints

| Method | Path                     | Description                     |
|--------|--------------------------|----------------------------------|
| GET    | `/`                      | Health check                    |
| GET    | `/api/products`          | List all products               |
| GET    | `/api/products/{id}`     | Get a single product            |
| POST   | `/api/products`          | Create a product                |
| POST   | `/api/cart`              | Add an item to the cart         |
| GET    | `/api/cart`              | View cart contents + total      |
| DELETE | `/api/cart/{product_id}` | Remove an item from the cart    |
| POST   | `/api/checkout`          | Clear the cart (checkout)       |

## Frontend features

- Lists products with live stock levels
- Add new products via a form
- Add products to the cart with a chosen quantity (respects stock limits)
- View cart with line totals and a running cart total
- Remove items from the cart
- Checkout, which clears the cart
- A small status indicator shows whether the API is reachable
