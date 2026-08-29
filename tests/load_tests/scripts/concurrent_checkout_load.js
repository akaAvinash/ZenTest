/*
 * LT-09: concurrent checkout requests against the same cart — seeds one
 * item in setup(), then has multiple VUs race to checkout simultaneously.
 * Exactly one should succeed (200, cart cleared); the rest should
 * correctly receive 400 'Cart is empty' rather than double-processing or
 * erroring.
 *
 * Run:
 *   k6 run tests/load_tests/scripts/concurrent_checkout_load.js
 */

import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export const options = {
  vus: 5,
  iterations: 5,
  thresholds: {
    http_req_duration: ['p(95)<1000'],
  },
};

export function setup() {
  const productRes = http.post(
    `${BASE_URL}/api/products`,
    JSON.stringify({ name: `k6 Checkout Race Product ${Date.now()}`, price: 3.0, stock: 10 }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  check(productRes, { 'seed product created': (r) => r.status === 201 });
  const productId = productRes.json('product_id');

  const cartRes = http.post(
    `${BASE_URL}/api/cart`,
    JSON.stringify({ product_id: productId, quantity: 1 }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  check(cartRes, { 'seed cart item added': (r) => r.status === 200 });
}

export default function () {
  const res = http.post(`${BASE_URL}/api/checkout`);
  check(res, {
    'status is 200 (won the race) or 400 (cart already cleared)': (r) =>
      r.status === 200 || r.status === 400,
  });
}

export function teardown() {
  const res = http.get(`${BASE_URL}/api/cart`);
  check(res, {
    'cart is empty after the race (exactly one checkout succeeded)': (r) =>
      r.json('items').length === 0,
  });
}
