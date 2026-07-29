package pii

# Flag obvious PII patterns in prompts/artifacts (defense in depth with Presidio).

deny[msg] {
  regex.match(`\b\d{3}-\d{2}-\d{4}\b`, input.content)
  msg := "SSN-like pattern detected"
}

deny[msg] {
  regex.match(`\b(?:\d[ -]*?){13,19}\b`, input.content)
  msg := "possible credit card number detected"
}

allow {
  count(deny) == 0
}
