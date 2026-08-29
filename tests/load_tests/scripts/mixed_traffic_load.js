/*
 * LT-08: mixed realistic traffic — each iteration randomly performs one
 * of three actions, weighted roughly like real usage: mostly browsing,
 * some adding to cart, occasional checkout.
 *
 * Run:
 *   k6 run tests/load_tests/scripts/mixed_traffic_load.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export const options = {
  vus: 10,
  duration: '30s',
  thresholds: {
    // Not http_req_failed — that flags every non-2xx as a failure, but
    // checkout legitimately 400s when the cart happens to be empty here.
    // The `checks` below already encode which outcomes are actually valid.
    checks: ['rate>0.99'],
    http_req_duration: ['p(95)<800'],
  },
};

export function setup() {
  const res = http.post(
    `${BASE_URL}/api/products`,
    JSON.stringify({ name: `k6 Mixed Traffic Product ${Date.now()}`, price: 2.5, stock: 1000000 }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  check(res, { 'seed product created': (r) => r.status === 201 });
  return { productId: res.json('product_id') };
}

export default function (data) {
  const roll = Math.random();

  if (roll < 0.6) {
    // 60%: browse products
    const res = http.get(`${BASE_URL}/api/products`);
    check(res, { 'browse: status 200': (r) => r.status === 200 });
  } else if (roll < 0.9) {
    // 30%: add to cart
    const res = http.post(
      `${BASE_URL}/api/cart`,
      JSON.stringify({ product_id: data.productId, quantity: 1 }),
      { headers: { 'Content-Type': 'application/json' } }
    );
    check(res, { 'add to cart: status 200': (r) => r.status === 200 });
  } else {
    // 10%: checkout (may legitimately 400 if the cart happens to be
    // empty at that moment — that's correct behavior, not a failure)
    const res = http.post(`${BASE_URL}/api/checkout`);
    check(res, { 'checkout: status 200 or 400': (r) => r.status === 200 || r.status === 400 });
  }

  sleep(1);
}
