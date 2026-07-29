package change_control_test

import data.change_control

test_release_needs_hitl {
  not change_control.allow with input as {
    "stage_id": "release_review",
    "phase": "exit",
    "hitl_approved": false,
  }
}

test_release_with_hitl {
  change_control.allow with input as {
    "stage_id": "release_review",
    "phase": "exit",
    "hitl_approved": true,
  }
}

test_impl_needs_design {
  not change_control.allow with input as {
    "stage_id": "implementation",
    "phase": "entry",
    "design_present": false,
  }
}
