package security_test

import data.security

test_allow_clean_code {
  security.allow with input as {
    "phase": "exit",
    "stage_id": "implementation",
    "content": "def shorten(url: str) -> str:\n    return url[:8]\n",
  }
}

test_deny_eval {
  not security.allow with input as {
    "phase": "exit",
    "stage_id": "implementation",
    "content": "x = eval(user_input)",
  }
}

test_deny_destructive_without_approval {
  not security.allow with input as {
    "phase": "entry",
    "requires_destructive": true,
    "approved": false,
  }
}
