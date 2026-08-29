# ZenTest — Inventory & Cart

A small FastAPI backend (products, cart, checkout) backed by SQLite, with a
plain HTML/CSS/JS frontend on top of it, plus a Playwright UI test suite and
a small CLI to run it. No frameworks or build step on the frontend — FastAPI
serves the static frontend directly, so the whole app is a single process,
locally and in production.

## Status

- **Backend & frontend:** working end to end — add products, add to cart
  (with stock validation and quantity merging), remove items, checkout, and
  clear the whole cart with a confirmation prompt. Frontend and API are
  served from a single FastAPI process (one port, no CORS juggling).
- **Deployment:** live at https://zentest-sael.onrender.com as a single
  Render web service (see `render.yaml` and the Deployment section below).
- **Test suite:** 3 automated Playwright UI tests passing (`test_api_status`,
  `test_new_product_appears_in_list`, `test_add_to_cart_shows_correct_total`),
  runnable via `pytest` directly or through `cli.py`, with self-contained
  HTML report generation.
- **Manual test cases:** 20 documented UI test cases covering the full
  frontend (product management, cart operations, validation/edge cases,
  empty states, the Clear Cart confirmation dialog, and toast feedback) —
  only 3 are automated so far.
- Known limitation: automated tests share the same `inventory.db` used for
  manual/dev testing rather than a dedicated disposable test database, so
  test-created products accumulate in it over time (test names are
  UUID-suffixed specifically to avoid collisions from this).

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
  logger.py                Framework-wide logger (backend, CLI, and tests all use this)
config/
  report_config.py          CLI's report-path helper (reports/zentest_report_<timestamp>)
tests/UI_tests/
  config.py                FRONTEND_URL / API_URL used by the tests
  conftest.py                Autouse fixture that clears the cart before/after each test
  pytest.ini                  Registers the "smoke" marker
  pages/                      Page objects (one class per page/section)
    base_page.py
    home_page.py
    products_page.py
    cart_page.py
  utils/
    api_helper.py             Direct API calls used to seed/clean test data
  tests/
    test_home_ui.py            API status indicator (smoke)
    test_products.py            Add product flow
    test_cart.py                 Add to cart / cart total flow
cli.py                    ZenTest CLI: list/run UI tests, generate HTML reports
render.yaml                Render deployment config (single web service)
requirements.txt           Backend dependencies (fastapi, uvicorn)
```

Note: there are two separate `utils/` and `config/` locations — the ones at
the repo root are framework-wide (usable from the backend, the CLI, and the
test suite alike), while the ones under `tests/UI_tests/` are specific to
that test suite (API helpers, target URLs). `utils` works from both without
collision since Python merges same-named packages found in different
locations (neither has an `__init__.py`); `config` doesn't merge the same
way, so `tests/UI_tests/config.py` intentionally takes priority within the
test suite over the root `config/` package.

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

`tests/UI_tests/config.py` points `FRONTEND_URL`/`API_URL` at the deployed
Render app by default, so tests run against the live site — no local server
needed. (Point both back at `http://127.0.0.1:8000` if you want to test
against a local run instead.)

```bash
pip install pytest pytest-playwright pytest-html requests
playwright install chromium

# via pytest directly
pytest --browser chromium

# via the CLI (also generates a self-contained HTML report under reports/)
python cli.py -m ui_test              # list all UI tests
python cli.py -m ui_test --smoke      # list only smoke-marked tests
python cli.py -m ui_test --start      # run all UI tests, generate report
python cli.py -m ui_test --smoke --start   # run smoke tests, generate report
```

Render's free tier spins down after 15 minutes idle, so the first test run
after a period of inactivity may take 30–60s longer while it wakes back up.

## Logging

`utils/logger.py` provides a shared `get_logger(name)` used across the
backend, the CLI, and the test suite (page objects, API helpers, fixtures).
Where the log file ends up depends on how things are run:

- `python cli.py -m ui_test --start` (or `--smoke --start`): each run's log
  is written to `reports/zentest_report_<timestamp>/zentest.log`, right
  alongside that run's `zentest_report.html` — so a report folder is fully
  self-contained (HTML report + screenshots/videos + logs).
- Anything else — the backend running standalone, or `pytest` run directly
  without the CLI — falls back to `logs/zentest.log` at the repo root.

See `TESTING.md` (local only, not committed) for full setup details,
troubleshooting, and what each test covers.
