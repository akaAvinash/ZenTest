/*
 * Write-path load test — POST /api/cart (add to cart) under concurrent load.
 * Uses setup() to seed one product with a huge stock count once, before the
 * load starts, so concurrent VUs adding to the same product don't trigger
 * the API's "insufficient stock" business-rule rejection — that's correct
 * behavior, not a performance failure, and would otherwise pollute the
 * error-rate metric with something unrelated to load.
 *
 * Note: every VU iteration adds a cart row and never checks out, so a local
 * inventory.db will accumulate cart entries — expected for a load test,
 * clear it via `python cli.py -m api_test` or the frontend's Clear Cart
 * button if it matters for your run.
 *
 * Run:
 *   k6 run tests/load_tests/scripts/cart_add_load.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export const options = {
  vus: 5,
  duration: '15s',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<800'],
  },
};

export function setup() {
  const res = http.post(
    `${BASE_URL}/api/products`,
    JSON.stringify({
      name: `k6 Load Test Product ${Date.now()}`,
      price: 1.0,
      stock: 1000000,
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  check(res, { 'seed product created': (r) => r.status === 201 });

  return { productId: res.json('product_id') };
}

export default function (data) {
  const res = http.post(
    `${BASE_URL}/api/cart`,
    JSON.stringify({ product_id: data.productId, quantity: 1 }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  check(res, {
    'status is 200': (r) => r.status === 200,
    'item added to cart': (r) => r.json('message') === 'Item added to cart',
  });

  sleep(1);
}
