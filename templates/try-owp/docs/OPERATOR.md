# Field Lab Operator Guide

This is the operator workflow for processing a submission while keeping lifecycle state in the service.

## 1. Read the queue

```bash
export OWP_FIELD_LAB_DB=/var/lib/owp-field-lab/owp-field-lab.sqlite3
python3 -m owp_field_lab.admin queue
```

Queue order is FIFO. Do not reorder by value signal.

## 2. Decide

Use `accept` only when the requested outcome is sufficiently clear and current __OWP_OPERATOR_NAME__ capability can responsibly attempt it. Otherwise use `pass` with a useful reason.

```bash
python3 -m owp_field_lab.admin accept OWP-... --note "Reason for taking it."
python3 -m owp_field_lab.admin pass OWP-... --reason "Reason for passing."
```

## 3. Start one numbered attempt

```bash
python3 -m owp_field_lab.admin start OWP-...
```

For PR work this refreshes the live GitHub snapshot first. If the PR changed while waiting, that change becomes a durable event before the attempt starts.

For idea work, the attempt begins from the recorded title, optional context URL and requested outcome.

## 4. Perform provider work outside the field-lab server

Use whatever agent/human stack is appropriate. Do not execute untrusted customer code inside the intake web process.

If a decision changes what should be built, record it as a question so the decision becomes part of the durable work record:

```bash
python3 -m owp_field_lab.admin ask OWP-... \
  --text "Which behavior should win?" \
  --option "A" \
  --option "B" \
  --evidence "https://..."
```

The work becomes parked until the customer answers from their private work thread.

## 5. Deliver only what exists

```bash
python3 -m owp_field_lab.admin deliver OWP-... \
  --summary "What was completed." \
  --evidence "https://github.com/.../commit/..." \
  --evidence "https://github.com/.../actions/runs/..."
```

Evidence must use HTTPS. A delivery without evidence is rejected by the service.

## 6. Validate separately

Record a named validation actor/tool and evidence:

```bash
python3 -m owp_field_lab.admin validate OWP-... \
  --result valid \
  --validator "fresh-clone-ci" \
  --evidence "https://..."
```

Use `invalid` when the delivery fails validation. Invalid sends the work back to `in_progress` for repair; it does not erase the failed delivery or validation history.

The field lab records actor separation but does not cryptographically prove organizational independence.

## 7. Let the customer rule

After `valid`, the customer sees three actions:

- **Approve** → completed;
- **Steer** → returns to `todo`; the next `start` creates a new attempt number;
- **Reject** → cancelled/rejected terminal result.

Do not change this result manually in SQLite.

## 8. Preserve portability

At any point:

```bash
python3 -m owp_field_lab.admin export-handoff OWP-... --out OWP-...-handoff.json
python3 -m owp_field_lab.admin verify-chain OWP-...
```

The customer can download the same token-free portable projection from the private tracking page.

## 9. Close the operating day

```bash
python3 -m owp_field_lab.admin verify-all
python3 -m owp_field_lab.admin backup \
  --out /var/backups/owp-field-lab/field-lab-$(date +%F-%H%M%S).sqlite3
```

If `verify-all` fails, stop mutating that database until the integrity failure is understood.
