package pii_test

import data.pii

test_ssn_denied {
  not pii.allow with input as {"content": "customer SSN 123-45-6789"}
}

test_clean_allowed {
  pii.allow with input as {"content": "Build a URL shortener with analytics"}
}
