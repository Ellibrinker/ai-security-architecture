# Regression demo

This synthetic fixture demonstrates the first deterministic semantic-diff
prototype without using a real application or customer data.

- `baseline.json`: a validated baseline where a Member cannot update another
  member's document.
- `changed.json`: the same structured model with one injected authorization
  regression: the non-owner Update rule changes from `deny` to `allow`.
- `expected_diff.json`: expected output from `src/semantic_diff.py`.

Run from the repository root:

```bash
python src/semantic_diff.py \
  examples/regression_demo/baseline.json \
  examples/regression_demo/changed.json \
  --output /tmp/regression_diff.json
```

The expected result is one `AUTHORIZATION_WEAKENING` regression candidate,
linked to the baseline invariant `inv_member_update_own_only`.
