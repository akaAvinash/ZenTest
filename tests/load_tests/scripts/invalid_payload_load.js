/*
 * LT-10: invalid payloads under load — every request deliberately sends a
 * negative price, checking the validation-rejection path stays fast and
 * consistent at volume, not just correct for a single request.
 *
 * Run:
 *   k6 run tests/load_tests/scripts/invalid_payload_load.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export const options = {
  vus: 10,
  duration: '15s',
  thresholds: {
    // Every request is EXPECTED to fail validation (422), so don't use
    // http_req_failed here — assert on the check() results instead via a
    // custom threshold on the 'checks' built-in metric.
    checks: ['rate>0.99'],
    http_req_duration: ['p(95)<500'],
  },
};

export default function () {
  const res = http.post(
    `${BASE_URL}/api/products`,
    JSON.stringify({ name: 'k6 Invalid Payload', price: -5, stock: 1 }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  check(res, {
    'status is 422 (validation rejected)': (r) => r.status === 422,
  });

  sleep(1);
}
