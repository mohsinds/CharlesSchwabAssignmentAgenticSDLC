package security

# Deny secrets, dangerous sinks, and unrestricted network in generated code.

deny[msg] {
  input.phase == "exit"
  input.stage_id == "implementation"
  contains(lower(input.content), "eval(")
  msg := "eval() is forbidden in generated code"
}

deny[msg] {
  input.phase == "exit"
  input.stage_id == "implementation"
  contains(lower(input.content), "pickle.loads")
  msg := "pickle.loads is forbidden"
}

deny[msg] {
  input.phase == "exit"
  input.stage_id == "implementation"
  contains(lower(input.content), "sk-")
  msg := "possible API key material in artifact"
}

deny[msg] {
  input.phase == "entry"
  input.requires_destructive == true
  input.approved != true
  msg := "destructive change requires explicit approval"
}

allow {
  count(deny) == 0
}
