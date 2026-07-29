package change_control

# High-impact stages require HITL flag or prior approval.

deny[msg] {
  input.stage_id == "release_review"
  input.phase == "exit"
  input.hitl_approved != true
  msg := "release_review requires human approval before exit"
}

deny[msg] {
  input.stage_id == "implementation"
  input.phase == "entry"
  input.design_present != true
  msg := "implementation entry requires design artifact"
}

allow {
  count(deny) == 0
}
