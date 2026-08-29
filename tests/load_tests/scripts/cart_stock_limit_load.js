/*
 * LT-07: concurrent add-to-cart against a single LOW-stock product —
 * verifies the API never oversells: the total ACCEPTED quantity across
 * all concurrent VUs must never exceed the seeded stock, and requests
 * beyond that must be correctly rejected with 400, not silently accepted.
 *
 * This is a correctness check disguised as a load test — deliberately
 * uses far more VUs than the stock can satisfy, so contention is
 * guaranteed, then verifies the outcome via a follow-up GET /api/cart in
 * teardown() rather than trusting individual response codes alone.
 *
 * Run:
 *   k6 run tests/load_tests/scripts/cart_stock_limit_load.js
 */

import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const SEEDED_STOCK = 10;

export const options = {
  vus: 20,
  iterations: 20, // each of the 20 VUs adds quantity 1, exactly once
  thresholds: {
    // Not a latency test — the real assertion is in teardown() below.
    // Still worth capping obviously-broken response times.
    http_req_duration: ['p(95)<1000'],
  },
};

export function setup() {
  const res = http.post(
    `${BASE_URL}/api/products`,
    JSON.stringify({
      name: `k6 Stock Limit Product ${Date.now()}`,
      price: 1.0,
      stock: SEEDED_STOCK,
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

  // Either outcome is valid individually — 200 (accepted, within stock) or
  // 400 (correctly rejected once stock is exhausted). What must NEVER
  // happen is a 200 that pushes the total past SEEDED_STOCK, which is
  // checked once, globally, in teardown() below.
  check(res, {
    'status is 200 or 400': (r) => r.status === 200 || r.status === 400,
  });
}

export function teardown(data) {
  const res = http.get(`${BASE_URL}/api/cart`);
  const cart = res.json();
  const item = cart.items.find((i) => i.product_id === data.productId);
  const totalAccepted = item ? item.quantity : 0;

  check(null, {
    [`total accepted quantity (${totalAccepted}) never exceeds seeded stock (${SEEDED_STOCK})`]: () =>
      totalAccepted <= SEEDED_STOCK,
  });
}
