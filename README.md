# ZenTest — Inventory & Cart

A small FastAPI backend (products, cart, checkout) backed by SQLite, with a
plain HTML/CSS/JS frontend on top of it, plus four test suites (UI, API,
database, load) and a small CLI to run them. No frameworks or build step on
the frontend — FastAPI serves the static frontend directly, so the whole
app is a single process, locally and in production.

## Status

- **Backend & frontend:** working end to end — add products, add to cart
  (with stock validation and quantity merging), remove items, checkout, and
  clear the whole cart with a confirmation prompt. Frontend and API are
  served from a single FastAPI process (one port, no CORS juggling).
- **Deployment:** live at https://zentest-sael.onrender.com as a single
  Render web service (see `render.yaml` and the Deployment section below).
- **Test suites:** 56 automated pytest tests passing — 17 Playwright UI
  tests, 20 API tests (via `ApiClient`), 19 direct-SQLite database tests —
  runnable via `pytest` directly or through `cli.py`, with self-contained
  HTML report generation. Plus 7 k6 load test scripts (read, write,
  concurrent product creation, stock-limit correctness under contention,
  mixed traffic, checkout race, invalid payloads at volume).
- **Manual test cases:** 20 documented cases each for UI, API, database,
  and load testing (see the generated PDFs) — every pytest suite now
  automates its full 20, and 7 of the 20 load cases are automated as k6
  scripts (the rest are CLI-flag variations of those scripts or one-off
  verification steps — see `TESTING.md`).
- Known limitation: `ui_tests`/`api_tests` share the same `inventory.db`
  used for manual/dev testing rather than a dedicated disposable test
  database, so test-created products accumulate in it over time (test names
  are UUID-suffixed to avoid collisions from this). `db_tests` cleans up
  after itself since it has direct DB access.

## Project structure

```
database/
  api.py                FastAPI app: product, cart, and checkout endpoints
  database.py            SQLite connection + schema (creates inventory.db on first run)
frontend/
  index.html              Page layout
  style.css               Styling
  app.js                  Talks to the API (fetch), renders products & cart
utils/
  logger.py                Framework-wide logger (backend, CLI, and all tests use this)
  config.py                 FRONTEND_URL / API_URL / report-path helper
  api_client.py               One method per backend endpoint (ApiClient) — the single
                               place that knows every URL/method/payload shape
  api_helper.py                 Thin convenience layer on top of ApiClient (used by fixtures)
  ocr_helper.py                   Wraps pytesseract — OCR on images/screenshots, for content
                                   a DOM selector can't reach
conftest.py                Root autouse fixture (cart reset) + pass/fail logging hook —
                            shared by ui_tests, api_tests, and db_tests
pytest.ini                 Registers the "smoke" marker
tests/
  ui_tests/
    pages/                    Page objects (one class per page/section)
      base_page.py
      home_page.py
      products_page.py
      cart_page.py
    tests/
      test_home_ui.py            API status indicator (smoke)
      test_products.py            Product list, currency format, out-of-stock state
      test_cart.py                 Cart totals, merging, removal, checkout, toasts
      test_clear_cart.py            Clear Cart confirm/cancel dialog
  api_tests/
    tests/
      test_health_api.py           Health check
      test_products_api.py         Products CRUD + validation edge cases
      test_cart_api.py              Cart/checkout happy paths + validation + 404s
  db_tests/
    conftest.py                  Opts out of the root's HTTP-based cart-reset fixture
    tests/
      test_database.py             Schema, constraints, joins, connections (19 tests)
  load_tests/
    scripts/                     7 k6 scripts — read/write throughput, concurrent
                                   product creation, stock-limit correctness under
                                   contention, mixed traffic, checkout race, invalid
                                   payloads at volume
cli.py                    ZenTest CLI: list/run pytest suites, generate HTML reports
render.yaml                Render deployment config (single web service)
requirements.txt           Backend dependencies (fastapi, uvicorn)
```

## Running locally

Everything — API and frontend — runs from one process:

```bash
pip install -r requirements.txt
python -m uvicorn database.api:app --reload --port 8000
```

Then open `http://127.0.0.1:8000` in a browser. This creates `inventory.db`
in the working directory on first run (it's gitignored — each environment
gets its own local database). Interactive API docs are at
`http://127.0.0.1:8000/docs`.

## API endpoints

| Method | Path                     | Description                          |
|--------|--------------------------|----------------------------------------|
| GET    | `/`                      | Frontend (serves `frontend/index.html`) |
| GET    | `/api/health`            | Health check                         |
| GET    | `/api/products`          | List all products                    |
| GET    | `/api/products/{id}`     | Get a single product                 |
| POST   | `/api/products`          | Create a product                     |
| POST   | `/api/cart`              | Add an item to the cart              |
| GET    | `/api/cart`              | View cart contents + total           |
| DELETE | `/api/cart/{product_id}` | Remove one item from the cart        |
| POST   | `/api/checkout`          | Checkout — clears the cart           |
| DELETE | `/api/delete`            | Clear the entire cart (no checkout)  |

## Frontend features

- Lists products with live stock levels
- Add new products via a form
- Add products to the cart with a chosen quantity (respects stock limits,
  merges quantity into the existing row if already in the cart)
- View cart with line totals and a running cart total
- Remove individual items from the cart
- Clear the whole cart, with a confirmation dialog before deleting
- Checkout, which clears the cart
- A small status indicator shows whether the API is reachable

## Deployment

Live at **https://zentest-sael.onrender.com** — deployed as a single Render
web service using `render.yaml` (see that file for the build/start
commands). Pushing to `main` redeploys automatically if the Render service
is connected to this GitHub repo.

**Known limitation:** the free plan's filesystem is not persistent —
`inventory.db` resets on every restart or redeploy. That's fine for a demo;
if you need data to survive restarts, upgrade to a plan with a persistent
disk or switch to a hosted database.

## Running the tests

`utils/config.py` points `FRONTEND_URL`/`API_URL` at the deployed Render
app by default, so `ui_tests`/`api_tests` run against the live site — no
local server needed. `db_tests` always runs against a local `inventory.db`
(it talks to SQLite directly, not over HTTP) and `load_tests` defaults to a
local server too (don't point sustained k6 load at the free-tier Render
deployment).

```bash
pip install pytest pytest-playwright pytest-html requests pytesseract
playwright install chromium

# via pytest directly — runs ui_tests + api_tests + db_tests
pytest --browser chromium

# via the CLI (also generates a self-contained HTML report under reports/)
python cli.py -m ui_test --start           # run UI tests, generate report
python cli.py -m api_test --start          # run API tests, generate report
python cli.py -m db_test --start           # run database tests, generate report
python cli.py -m ui_test --smoke --start   # run smoke-marked UI tests, generate report

# load tests (k6, separate from pytest) — see TESTING.md for the full list
k6 run tests/load_tests/scripts/products_read_load.js
k6 run tests/load_tests/scripts/cart_stock_limit_load.js
```

Render's free tier spins down after 15 minutes idle, so the first test run
after a period of inactivity may take 30–60s longer while it wakes back up.

## Logging

`utils/logger.py` provides a shared `get_logger(name)` used across the
backend, the CLI, and all three pytest suites (page objects, API helpers,
fixtures). Where the log file ends up depends on how things are run:

- `python cli.py -m <ui_test|api_test|db_test> --start`: each run's log is
  written to `reports/zentest_report_<timestamp>/zentest.log`, right
  alongside that run's `zentest_report.html` — so a report folder is fully
  self-contained (HTML report + screenshots/videos + logs).
- Anything else — the backend running standalone, or `pytest` run directly
  without the CLI — falls back to `logs/zentest.log` at the repo root.

See `TESTING.md` and `HISTORY.md` (local only, not committed) for full
setup details, troubleshooting, and the stage-by-stage story of how this
framework got built.
