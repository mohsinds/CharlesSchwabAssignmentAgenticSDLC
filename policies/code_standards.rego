package code_standards

deny[msg] {
  input.phase == "exit"
  input.stage_id == "implementation"
  input.ast_ok == false
  msg := "AST parse failed"
}

deny[msg] {
  input.phase == "exit"
  input.stage_id == "implementation"
  input.ruff_ok == false
  msg := "ruff lint failed"
}

deny[msg] {
  input.phase == "exit"
  input.stage_id == "test"
  input.pytest_ok == false
  msg := "pytest failed"
}

deny[msg] {
  input.phase == "exit"
  input.stage_id == "test"
  input.coverage != null
  input.coverage < input.coverage_min
  msg := sprintf("coverage %.2f below minimum %.2f", [input.coverage, input.coverage_min])
}

allow {
  count(deny) == 0
}
