import time
import pytest

from app.schemas.context import RegulatoryContext
from app.schemas.definition import ApplicabilityRule, SlotBlueprint, SlotGuidance
from app.services.definition_service import definition_service
from app.services.rules_engine import RulesEngine, rules_engine


def test_tc_ur01_01_statutory_risk_class_guardrails():
    """TC-UR01-01: Verifies statutory jurisdiction constraints on risk classes.

    Form MD-7 and MD-8 (Central Licensing Authority) only permit Class C and Class D.
    Form MD-3 and MD-4 (State Licensing Authority) only permit Class A and Class B.
    Form MD-14 (Import) permits all four classes (A, B, C, D).
    """
    # Form MD-7 rejection on Class A & Class B
    valid, err = rules_engine.validate_pathway_constraints(
        "MD-7", {"risk_class": "CLASS_A"}
    )
    assert not valid
    assert "Form MD-7 is restricted to Class C and Class D" in err

    valid, err = rules_engine.validate_pathway_constraints(
        "MD-7", {"risk_class": "CLASS_B"}
    )
    assert not valid

    # Form MD-7 acceptance on Class C & Class D
    valid, err = rules_engine.validate_pathway_constraints(
        "MD-7", {"risk_class": "CLASS_C"}
    )
    assert valid
    assert err is None

    valid, err = rules_engine.validate_pathway_constraints(
        "MD-7", {"risk_class": "CLASS_D"}
    )
    assert valid

    # Form MD-3 rejection on Class C & Class D
    valid, err = rules_engine.validate_pathway_constraints(
        "MD-3", {"risk_class": "CLASS_C"}
    )
    assert not valid
    assert "Form MD-3 is restricted to Class A and Class B" in err

    # Form MD-3 acceptance on Class A & Class B
    valid, err = rules_engine.validate_pathway_constraints(
        "MD-3", {"risk_class": "CLASS_A"}
    )
    assert valid

    # Form MD-14 acceptance on all risk classes
    for rc in ["CLASS_A", "CLASS_B", "CLASS_C", "CLASS_D"]:
        valid, err = rules_engine.validate_pathway_constraints(
            "MD-14", {"risk_class": rc}
        )
        assert valid

    # Test Licence MD-12 cannot be RETENTION
    valid, err = rules_engine.validate_pathway_constraints(
        "MD-12", {"risk_class": "CLASS_C", "filing_modality": "RETENTION"}
    )
    assert not valid
    assert "does not support RETENTION" in err


def test_tc_ur01_02_sterility_dynamic_slot_activation_md14():
    """TC-UR01-02: Verifies dynamic activation and deactivation of sterilization slot in MD-14.

    When is_sterile is False, Slot 10.14 (Sterilization Validation) must be NOT_APPLICABLE.
    When is_sterile is True, Slot 10.14 must transition to active MISSING.
    """
    bp = definition_service.get_blueprint("MD-14")
    slot_10_14 = definition_service.get_slot_by_id(bp, "10.14")
    assert slot_10_14 is not None

    # Case 1: Non-sterile device
    ctx_non_sterile = RegulatoryContext(is_sterile=False)
    eval_non_sterile = rules_engine.evaluate_slot(slot_10_14, ctx_non_sterile)
    assert not eval_non_sterile.is_active
    assert eval_non_sterile.status == "NOT_APPLICABLE"
    assert "Deactivated by statutory predicate" in eval_non_sterile.deactivation_reason

    # Case 2: Sterile device
    ctx_sterile = RegulatoryContext(is_sterile=True)
    eval_sterile = rules_engine.evaluate_slot(slot_10_14, ctx_sterile)
    assert eval_sterile.is_active
    assert eval_sterile.status == "MISSING"
    assert eval_sterile.deactivation_reason is None


def test_sterility_dynamic_slot_activation_md7():
    """Verifies dynamic activation of sterilization slot in Form MD-7 (Slot 8.14)."""
    bp = definition_service.get_blueprint("MD-7")
    slot_8_14 = definition_service.get_slot_by_id(bp, "8.14")
    assert slot_8_14 is not None

    # Non-sterile
    eval_non_sterile = rules_engine.evaluate_slot(slot_8_14, {"is_sterile": False})
    assert not eval_non_sterile.is_active
    assert eval_non_sterile.status == "NOT_APPLICABLE"

    # Sterile
    eval_sterile = rules_engine.evaluate_slot(slot_8_14, {"is_sterile": True})
    assert eval_sterile.is_active
    assert eval_sterile.status == "OPTIONAL"



def test_software_predicate_and_alias_resolution():
    """Verifies software/SaMD slot activation and field alias resolution."""
    bp = definition_service.get_blueprint("MD-14")
    slot_software = definition_service.get_slot_by_id(bp, "10.15")

    # Inactive by default
    eval_default = rules_engine.evaluate_slot(slot_software, {})
    assert not eval_default.is_active

    # Active via has_software=True
    eval_active = rules_engine.evaluate_slot(slot_software, {"has_software": True})
    assert eval_active.is_active

    # Active via alias is_samd=True
    eval_alias = rules_engine.evaluate_slot(slot_software, {"is_samd": True})
    assert eval_alias.is_active


def test_medicinal_substance_predicate_and_alias():
    """Verifies medicinal substance slot activation and field alias resolution."""
    bp = definition_service.get_blueprint("MD-14")
    slot_drug = definition_service.get_slot_by_id(bp, "10.12")

    assert not rules_engine.evaluate_slot(slot_drug, {}).is_active
    assert rules_engine.evaluate_slot(
        slot_drug, {"has_medicinal_substance": True}
    ).is_active
    assert rules_engine.evaluate_slot(
        slot_drug, {"has_drug_substance": True}
    ).is_active


def test_animal_origin_and_investigational_predicates():
    """Verifies animal origin (Slot 10.13) and investigational (Slot 12.0) activation."""
    bp = definition_service.get_blueprint("MD-14")
    slot_animal = definition_service.get_slot_by_id(bp, "10.13")
    slot_investigational = definition_service.get_slot_by_id(bp, "12.0")

    assert not rules_engine.evaluate_slot(slot_animal, {}).is_active
    assert rules_engine.evaluate_slot(
        slot_animal, {"has_animal_origin": True}
    ).is_active

    assert not rules_engine.evaluate_slot(slot_investigational, {}).is_active
    assert rules_engine.evaluate_slot(
        slot_investigational, {"is_investigational": True}
    ).is_active


def test_nested_dot_notation_extraction():
    """Verifies extracting nested dictionary fields like ivd_parameters.is_veterinary."""
    rule = ApplicabilityRule(
        field="ivd_parameters.is_veterinary",
        operator="EQUALS",
        value=True,
    )

    ctx_false = {"ivd_parameters": {"is_veterinary": False}}
    assert not RulesEngine.evaluate_rule(rule, ctx_false)

    ctx_true = {"ivd_parameters": {"is_veterinary": True}}
    assert RulesEngine.evaluate_rule(rule, ctx_true)

    ctx_missing = {}
    assert not RulesEngine.evaluate_rule(rule, ctx_missing)


def test_rule_operators_comprehensive():
    """Verifies EQUALS, NOT_EQUALS, IN, NOT_IN, GREATER_THAN, LESS_THAN, ALWAYS_TRUE, ALWAYS_FALSE."""
    # ALWAYS_TRUE and ALWAYS_FALSE
    assert RulesEngine.evaluate_rule(
        ApplicabilityRule(condition="ALWAYS_TRUE"), {}
    )
    assert not RulesEngine.evaluate_rule(
        ApplicabilityRule(condition="ALWAYS_FALSE"), {}
    )

    # NOT_EQUALS
    rule_neq = ApplicabilityRule(
        field="risk_class", operator="NOT_EQUALS", value="CLASS_A"
    )
    assert RulesEngine.evaluate_rule(rule_neq, {"risk_class": "CLASS_C"})
    assert not RulesEngine.evaluate_rule(rule_neq, {"risk_class": "CLASS_A"})

    # IN and NOT_IN
    rule_in = ApplicabilityRule(
        field="risk_class", operator="IN", value=["CLASS_C", "CLASS_D"]
    )
    assert RulesEngine.evaluate_rule(rule_in, {"risk_class": "CLASS_C"})
    assert not RulesEngine.evaluate_rule(rule_in, {"risk_class": "CLASS_B"})

    rule_notin = ApplicabilityRule(
        field="risk_class", operator="NOT_IN", value=["CLASS_A", "CLASS_B"]
    )
    assert RulesEngine.evaluate_rule(rule_notin, {"risk_class": "CLASS_C"})
    assert not RulesEngine.evaluate_rule(rule_notin, {"risk_class": "CLASS_A"})

    # GREATER_THAN and LESS_THAN
    rule_gt = ApplicabilityRule(field="score", operator="GREATER_THAN", value=10)
    assert RulesEngine.evaluate_rule(rule_gt, {"score": 15})
    assert not RulesEngine.evaluate_rule(rule_gt, {"score": 5})

    rule_lt = ApplicabilityRule(field="score", operator="LESS_THAN", value=10)
    assert RulesEngine.evaluate_rule(rule_lt, {"score": 5})
    assert not RulesEngine.evaluate_rule(rule_lt, {"score": 15})


def test_evaluate_blueprint_slots_and_filter_active():
    """Verifies batch slot evaluation and active slot filtering."""
    bp = definition_service.get_blueprint("MD-14")

    # In baseline non-sterile non-software context, 6 slots are deactivated
    ctx_baseline = RegulatoryContext(is_sterile=False, has_software=False)
    evaluated = rules_engine.evaluate_blueprint_slots(bp, ctx_baseline)
    assert len(evaluated) == 36

    active_evaluated = [s for s in evaluated if s.is_active]
    inactive_evaluated = [s for s in evaluated if not s.is_active]
    assert len(active_evaluated) == 30
    assert len(inactive_evaluated) == 6

    # Verify filter_active_slots helper returns the exact active slot objects
    active_slots = rules_engine.filter_active_slots(bp, ctx_baseline)
    assert len(active_slots) == 30
    assert all(isinstance(s, SlotBlueprint) for s in active_slots)

    # When all conditional flags are True, all 36 slots must be active
    ctx_full = RegulatoryContext(
        is_sterile=True,
        has_software=True,
        has_medicinal_substance=True,
        has_animal_origin=True,
        has_animal_studies=True,
        is_investigational=True,
    )
    evaluated_full = rules_engine.evaluate_blueprint_slots(bp, ctx_full)
    assert all(s.is_active for s in evaluated_full)
    assert sum(1 for s in evaluated_full if s.status == "NOT_APPLICABLE") == 0


def test_tc_nfr_01_rules_engine_latency_benchmark():
    """TC-NFR-01: Verifies rule evaluation executes well under 200ms latency requirement.

    Executes 500 slot evaluations and measures total execution time.
    """
    bp = definition_service.get_blueprint("MD-14")
    ctx = RegulatoryContext(is_sterile=True, has_software=True)

    start_time = time.perf_counter()
    # Execute 500 complete blueprint evaluations (18,000 discrete slot evaluations)
    for _ in range(500):
        _ = rules_engine.evaluate_blueprint_slots(bp, ctx)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    # NFR requires 500 evaluations in < 200ms
    assert (
        elapsed_ms < 200.0
    ), f"Rules evaluation exceeded performance ceiling: {elapsed_ms:.2f}ms"
