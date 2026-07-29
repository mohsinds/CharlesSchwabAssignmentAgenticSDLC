package code_standards_test

import data.code_standards

test_ast_fail {
  not code_standards.allow with input as {
    "phase": "exit",
    "stage_id": "implementation",
    "ast_ok": false,
  }
}

test_coverage_fail {
  not code_standards.allow with input as {
    "phase": "exit",
    "stage_id": "test",
    "pytest_ok": true,
    "coverage": 0.4,
    "coverage_min": 0.6,
  }
}

test_test_pass {
  code_standards.allow with input as {
    "phase": "exit",
    "stage_id": "test",
    "pytest_ok": true,
    "coverage": 0.8,
    "coverage_min": 0.6,
  }
}
