# OWP Field Lab — executable feature map

This file maps every material public/product promise in the minimum field-lab slice to executable coverage in `tests/test_field_lab.py` or to the release smoke script.

## Intake and work vocabulary

| Behavior | Test coverage |
|---|---|
| Open GitHub PRs are parsed safely, canonicalized and verified through GitHub's pulls API | `test_pr_url_parser_canonicalizes_identity_and_rejects_unsafe_forms`, `test_real_verifier_constructs_only_github_api_request_and_snapshots_size`, `test_closed_pr_and_missing_head_are_rejected` |
| GitHub API rate limiting produces an actionable failure | `test_rate_limited_github_response_is_actionable` |
| Greenfield ideas enter the same durable work system without invented GitHub metadata | `test_idea_submission_runs_without_github_and_enters_same_queue`, `test_idea_submission_over_http_and_customer_handoff_download` |
| Idea title and optional context URL are bounded/safe | `test_idea_title_and_context_url_are_validated` |
| Exact USD value signal is stored as integer cents; malformed/non-money values fail | `test_exact_usd_bid_is_integer_cents_and_rejects_non_money` |
| Submission requires authorization and disclosed field-data use acknowledgement | `test_submission_requires_authorization_and_data_use_attestation`, `test_submission_requires_attestation_over_http` |
| HTTP mutations require JSON rather than browser-simple cross-site form bodies | `test_submission_requires_application_json_to_block_cross_site_simple_posts` |
| Small and very large PRs may both enter; size is a signal, not an eligibility gate | `test_small_and_very_large_prs_are_both_allowed` |

## Private working set and capacity

| Behavior | Test coverage |
|---|---|
| Queue maximum cannot be configured above 20 | `test_queue_max_is_hard_capped_at_twenty` |
| Active queue is hard-capped at 20 | `test_private_queue_enforces_exact_max_20` |
| Concurrent intake cannot overfill the 20 slots | `test_concurrent_submissions_cannot_overfill_20_slots` |
| Concurrent/case-variant duplicate PRs cannot consume multiple active slots | `test_concurrent_duplicate_pr_submissions_consume_only_one_slot`, `test_case_variant_duplicate_pr_cannot_consume_another_slot` |
| Queue is FIFO and value signal never ranks it | `test_private_queue_is_received_order_not_bid_ranked` |
| Public status exposes aggregate capacity, not private queue contents | `test_public_status_exposes_capacity_not_private_queue`, `test_public_http_has_no_admin_queue_surface` |
| Live SSE capacity changes after intake and simultaneous streams are bounded | `test_sse_capacity_live_updates_after_submission`, `test_sse_connection_count_is_bounded` |
| Submission attempts are throttled | `test_submission_rate_limiter_returns_429_and_retry_after` |
| Browser UI cannot accidentally re-enable submission while full | `test_full_queue_cannot_be_accidentally_reenabled_after_submit` |

## Provider lifecycle

| Behavior | Test coverage |
|---|---|
| ACCEPT starts explicit provider ownership; PASS closes and frees capacity | `test_accept_start_question_answer_flow`, `test_provider_pass_is_terminal_and_reopens_capacity` |
| Attempts are numbered | `test_accept_start_question_answer_flow`, `test_customer_steer_requires_instruction_and_creates_another_attempt` |
| PR head/size are re-verified immediately before work begins | `test_attempt_start_refreshes_moved_pr_head_before_work_begins` |
| Ideas can run through accept/start/delivery/validation with no GitHub dependency | `test_idea_accept_start_delivery_validation_and_customer_approval` |
| Questions require distinct options and safe evidence links | `test_question_requires_distinct_options_and_https_evidence` |
| Customer answers are durable and resume parked work | `test_accept_start_question_answer_flow` |
| Delivery requires HTTPS evidence | `test_delivery_requires_https_evidence` |
| Validation requires a named actor and evidence; invalid validation routes to repair | `test_validation_requires_named_actor_and_invalid_routes_to_repair` |

## Customer disposition and portability

| Behavior | Test coverage |
|---|---|
| A valid delivery still requires customer disposition | `test_valid_delivery_requires_customer_disposition` |
| STEER requires an instruction and creates a new attempt boundary | `test_customer_steer_requires_instruction_and_creates_another_attempt` |
| REJECT requires a reason, closes work and frees capacity | `test_customer_reject_requires_reason_and_frees_slot` |
| Customer work views require the secret claim token | `test_claim_token_is_required_for_customer_view` |
| Wrong token and unknown ref are indistinguishable over HTTP | `test_wrong_token_and_unknown_ref_share_same_not_found_response` |
| Work URL routing is exact | `test_work_routes_are_exact_not_prefix_matches` |
| Portable handoff contains work state/history but no claim secret | `test_handoff_export_is_portable_and_contains_no_claim_secret`, `test_customer_handoff_for_idea_is_token_protected_and_token_free`, `test_idea_submission_over_http_and_customer_handoff_download` |
| Browser offers inline answer/disposition controls and handoff download without blocking prompt dialogs | `test_customer_decisions_use_inline_controls_and_handoff_download` |

## Durability, integrity and field data

| Behavior | Test coverage |
|---|---|
| Intake snapshots real PR metadata, hashes customer token, and tightens DB permissions | `test_submit_records_real_pr_snapshot_hashes_token_and_tightens_db_permissions` |
| Work queue/event state survives service restart | `test_queue_and_event_state_survive_service_restart` |
| Event-chain tampering is detected and surfaced | `test_hash_linked_event_chain_detects_tampering_and_projection_surfaces_warning`, `test_verify_all_catches_event_tampering`, `test_healthz_fails_when_event_chain_is_corrupted` |
| Consistent SQLite backup reopens and verifies | `test_consistent_database_backup_can_be_reopened_and_verified` |
| Value-signal export preserves source/size signal | `test_bid_export_pairs_market_signal_with_pr_size` |
| Private research export pairs requested outcome/value/lifecycle without claim secret | `test_private_research_export_pairs_value_with_requested_outcome_without_secret` |
| Operator CLI drives the persisted idea lifecycle and refuses to create a new empty DB silently on a wrong path | `test_operator_cli_drives_core_idea_lifecycle_on_real_database`, `test_operator_cli_refuses_to_silently_create_missing_database` |

## Public experience and protocol boundary

| Behavior | Test coverage |
|---|---|
| Landing page explains no-charge value/data boundary and supports PR + idea work | `test_static_page_and_privacy_notice_are_explicit`, `test_public_form_discloses_free_service_data_use_and_authorization` |
| Responsive layout includes capacity and lifecycle UI | `test_polished_layout_has_mobile_breakpoints_capacity_and_lifecycle` |
| Static and JSON responses carry security headers | `test_security_headers_are_sent_on_static_and_json` |
| Machine-readable surface declares profile, two work types, lifecycle and no conformance claim | `test_machine_readable_surface_describes_field_lab_boundary` |
| Complete PR-oriented service journey exists | `test_full_golden_journey` |
| Complete idea journey exists | `test_idea_accept_start_delivery_validation_and_customer_approval` |
| Cross-boundary journey crosses HTTP customer intake/actions, private operator lifecycle and authenticated handoff | `test_complete_idea_journey_crosses_http_operator_customer_and_handoff` |

## Release/package contract

`scripts/smoke.sh` additionally verifies:

- complete unit/integration/security/static suite passes;
- Python sources compile;
- server/admin entry points load;
- JavaScript syntax is checked when Node is available;
- every path in `PACKAGE_FILES.txt` exists and there are no undeclared release files;
- required deployment, privacy, operator and profile documents are boxed;
- public contract anchors are present.

`scripts/live-github-smoke.sh` is the separate outbound-network check for a public PR when run on a host with GitHub access.

| Configurable durable provider actor is written into provider lifecycle events | `test_configurable_provider_actor_is_recorded` |
