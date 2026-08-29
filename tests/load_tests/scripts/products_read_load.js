/*
 * Read-only load test — GET /api/products under concurrent load.
 * Safe to run repeatedly: it never mutates any data.
 *
 * Run:
 *   k6 run tests/load_tests/scripts/products_read_load.js
 *
 * Point at a different target (e.g. the deployed Render app — use with
 * caution, it's a shared free-tier instance, not built for load testing):
 *   k6 run -e BASE_URL=https://zentest-sael.onrender.com tests/load_tests/scripts/products_read_load.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';

// Defaults to a local run — don't point sustained load at the free-tier
// Render deployment unless you mean to.
const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export const options = {
  vus: 5,
  duration: '15s',
  thresholds: {
    http_req_failed: ['rate<0.01'], // fewer than 1% of requests may fail
    http_req_duration: ['p(95)<500'], // 95% of requests must complete under 500ms
  },
};

export default function () {
  const res = http.get(`${BASE_URL}/api/products`);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response is a JSON array': (r) => {
      try {
        return Array.isArray(r.json());
      } catch {
        return false;
      }
    },
  });

  sleep(1);
}
