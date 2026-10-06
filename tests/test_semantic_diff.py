import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from semantic_diff import compare_models  # noqa: E402


def rule(effect="deny", *, conditions=None, status="CONFIRMED"):
    return {
        "id": "rule_member_update_other",
        "actor": "actor_member",
        "resource": "resource_document",
        "action": "Update",
        "conditions": conditions or ["same organization", "not owner"],
        "effect": effect,
        "execution_path_status": "OBSERVED_IN_USE",
        "status": status,
        "confidence": 90,
        "evidence": "test evidence",
        "evidence_source": "test",
    }


def model(rule_value, *, invariant=True):
    return {
        "schema_version": "1.1.0",
        "authorization_rules": [rule_value],
        "security_invariants": [
            {
                "id": "inv_member_own_only",
                "statement": "Members may only update documents they own.",
                "affected_actors": ["actor_member"],
                "affected_resources": ["resource_document"],
                "affected_actions": ["Update"],
                "status": "CONFIRMED",
            }
        ] if invariant else [],
    }


class SemanticDiffTests(unittest.TestCase):
    def test_deny_to_allow_is_weakening_and_candidate(self):
        result = compare_models(
            model(rule("deny")),
            model(rule("allow", status="OBSERVED")),
        )
        change = result["changes"][0]
        self.assertEqual(change["type"], "AUTHORIZATION_WEAKENING")
        self.assertTrue(change["regression_candidate"])
        self.assertEqual(
            change["related_invariants"][0]["id"],
            "inv_member_own_only",
        )

    def test_allow_to_deny_is_restriction_not_regression(self):
        result = compare_models(model(rule("allow")), model(rule("deny")))
        change = result["changes"][0]
        self.assertEqual(change["type"], "AUTHORIZATION_RESTRICTION")
        self.assertFalse(change["regression_candidate"])

    def test_same_effect_produces_no_change(self):
        result = compare_models(model(rule("deny")), model(rule("deny")))
        self.assertEqual(result["changes"], [])

    def test_confidence_or_status_only_change_is_ignored(self):
        before = rule("deny", status="INFERRED")
        after = dict(before, confidence=100, status="CONFIRMED")
        result = compare_models(model(before), model(after))
        self.assertEqual(result["changes"], [])

    def test_condition_order_does_not_create_false_diff(self):
        before = rule(
            "deny",
            conditions=["same organization", "not owner"],
        )
        after = rule(
            "deny",
            conditions=["not owner", "same organization"],
        )
        result = compare_models(model(before), model(after))
        self.assertEqual(result["changes"], [])

    def test_unknown_to_deny_is_new_evidence_not_regression(self):
        result = compare_models(
            model(rule("unknown", status="UNRESOLVED")),
            model(rule("deny", status="CONFIRMED")),
        )
        change = result["changes"][0]
        self.assertEqual(change["type"], "NEWLY_OBSERVED_DENY")
        self.assertFalse(change["regression_candidate"])

    def test_rule_addition_is_reported(self):
        baseline = {
            "schema_version": "1.1.0",
            "authorization_rules": [],
            "security_invariants": [],
        }
        current = model(rule("allow"))
        result = compare_models(baseline, current)
        self.assertEqual(result["changes"][0]["type"], "RULE_ADDED")


    def test_rule_removal_is_reported_not_regression(self):
        baseline = model(rule("deny"))
        current = {
            "schema_version": "1.1.0",
            "authorization_rules": [],
            "security_invariants": [],
        }
        result = compare_models(baseline, current)
        change = result["changes"][0]
        self.assertEqual(change["type"], "RULE_REMOVED")
        self.assertFalse(change["regression_candidate"])
        self.assertEqual(result["summary"]["rules_removed"], 1)

    def test_unknown_to_allow_is_new_evidence_not_regression(self):
        result = compare_models(
            model(rule("unknown", status="UNRESOLVED")),
            model(rule("allow", status="OBSERVED")),
        )
        change = result["changes"][0]
        self.assertEqual(change["type"], "NEWLY_OBSERVED_ALLOW")
        self.assertFalse(change["regression_candidate"])

    def test_known_to_unknown_is_unresolved_not_regression(self):
        for before in ("allow", "deny"):
            with self.subTest(before=before):
                result = compare_models(
                    model(rule(before)),
                    model(rule("unknown", status="UNRESOLVED")),
                )
                change = result["changes"][0]
                self.assertEqual(change["type"], "AUTHORIZATION_BECAME_UNRESOLVED")
                self.assertFalse(change["regression_candidate"])

    def test_reworded_condition_is_removal_plus_addition(self):
        before = rule("deny", conditions=["same organization", "not owner"])
        after = rule("deny", conditions=["same organization", "actor is not the owner"])
        result = compare_models(model(before), model(after))
        types = sorted(c["type"] for c in result["changes"])
        self.assertEqual(types, ["RULE_ADDED", "RULE_REMOVED"])
        self.assertEqual(result["summary"]["regression_candidates"], 0)

    def test_duplicate_semantic_rule_identity_raises(self):
        first = rule("deny", conditions=["same organization", "not owner"])
        second = dict(
            rule("allow", conditions=["Not  Owner", "same organization"]),
            id="rule_member_update_other_duplicate",
        )
        duplicate = model(first)
        duplicate["authorization_rules"].append(second)
        with self.assertRaises(ValueError):
            compare_models(duplicate, model(first))

if __name__ == "__main__":
    unittest.main()
