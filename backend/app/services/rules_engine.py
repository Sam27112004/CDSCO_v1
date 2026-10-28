"""Statutory Rules Engine.

Evaluates MDR 2017 statutory pathway guardrails, risk class constraints, and dynamic
slot applicability predicates based on submission regulatory context.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from app.schemas.context import EvaluatedSlot, RegulatoryContext
from app.schemas.definition import (
    ApplicabilityRule,
    FormBlueprint,
    SlotBlueprint,
)

logger = logging.getLogger(__name__)

# Field aliases for regulatory context flexibility
FIELD_ALIASES: Dict[str, str] = {
    "is_samd": "has_software",
    "has_software": "is_samd",
    "has_drug_substance": "has_medicinal_substance",
    "has_medicinal_substance": "has_drug_substance",
}


class StatutoryConstraintError(ValueError):
    """Raised when a submission violates MDR 2017 legal route constraints."""

    pass


class RulesEngine:
    """Predicate evaluator and statutory constraint validator."""

    @staticmethod
    def validate_pathway_constraints(
        definition_code: str,
        regulatory_context: Union[Dict[str, Any], RegulatoryContext],
    ) -> Tuple[bool, Optional[str]]:
        """Validates that a submission's risk class and modality adhere to MDR 2017 jurisdiction rules.

        Args:
            definition_code: Statutory form code (e.g. 'MD-14', 'MD-7', 'MD-3').
            regulatory_context: Context dictionary or RegulatoryContext model.

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str]).
        """
        code = definition_code.strip().upper()
        if isinstance(regulatory_context, RegulatoryContext):
            ctx = regulatory_context.model_dump()
        else:
            ctx = dict(regulatory_context)

        risk_class = ctx.get("risk_class", "CLASS_C")
        modality = ctx.get("filing_modality", "FRESH")

        # Guardrail 1: Form MD-7 and Form MD-8 (CLA Commercial / Loan Manufacturing)
        # Restricted strictly to Class C and Class D
        if code in ["MD-7", "MD-8"]:
            if risk_class in ["CLASS_A", "CLASS_B"]:
                return (
                    False,
                    f"Form {code} is restricted to Class C and Class D commercial manufacturing under Central Licensing Authority jurisdiction.",
                )

        # Guardrail 2: Form MD-3 and Form MD-4 (SLA Commercial / Loan Manufacturing)
        # Restricted strictly to Class A and Class B under State Licensing Authority
        if code in ["MD-3", "MD-4"]:
            if risk_class in ["CLASS_C", "CLASS_D"]:
                return (
                    False,
                    f"Form {code} is restricted to Class A and Class B manufacturing under State Licensing Authority jurisdiction.",
                )

        # Guardrail 3: Test Licences (MD-12, MD-16) cannot have RETENTION modality
        if code in ["MD-12", "MD-16"]:
            if modality == "RETENTION":
                return (
                    False,
                    f"Form {code} is a test licence and does not support RETENTION filing modality.",
                )

        return (True, None)

    @classmethod
    def extract_field_value(
        cls,
        context_dict: Dict[str, Any],
        field_path: str,
    ) -> Any:
        """Extracts a field value from context dictionary supporting dot notation and aliases.

        Args:
            context_dict: Dictionary containing context parameters.
            field_path: Dot-separated path or field name (e.g. 'is_sterile', 'ivd_parameters.is_veterinary').

        Returns:
            Extracted value or None if field is missing.
        """
        if not field_path:
            return None

        parts = field_path.split(".")
        current = context_dict

        for part in parts:
            if isinstance(current, dict):
                if part in current:
                    current = current[part]
                else:
                    # Check field aliases
                    alias = FIELD_ALIASES.get(part)
                    if alias and alias in current:
                        current = current[alias]
                    else:
                        return None
            else:
                return None

        return current

    @classmethod
    def evaluate_rule(
        cls,
        rule: Optional[ApplicabilityRule],
        regulatory_context: Union[Dict[str, Any], RegulatoryContext],
    ) -> bool:
        """Evaluates an ApplicabilityRule predicate against regulatory context.

        Args:
            rule: ApplicabilityRule instance or None.
            regulatory_context: Submission regulatory parameters.

        Returns:
            True if slot is applicable/active, False if inactive.
        """
        if rule is None:
            return True

        if rule.condition == "ALWAYS_TRUE":
            return True
        if rule.condition == "ALWAYS_FALSE":
            return False

        # If no field is specified and condition is unset, default to applicable
        if not rule.field:
            return True

        ctx = (
            regulatory_context.model_dump()
            if isinstance(regulatory_context, RegulatoryContext)
            else dict(regulatory_context)
        )

        actual_val = cls.extract_field_value(ctx, rule.field)
        target_val = rule.value
        op = rule.operator or "EQUALS"

        if op == "EQUALS":
            return bool(actual_val == target_val)
        elif op == "NOT_EQUALS":
            return bool(actual_val != target_val)
        elif op == "IN":
            if isinstance(target_val, (list, tuple, set)):
                return actual_val in target_val
            return actual_val == target_val
        elif op == "NOT_IN":
            if isinstance(target_val, (list, tuple, set)):
                return actual_val not in target_val
            return actual_val != target_val
        elif op == "GREATER_THAN":
            if actual_val is None or target_val is None:
                return False
            return bool(actual_val > target_val)
        elif op == "LESS_THAN":
            if actual_val is None or target_val is None:
                return False
            return bool(actual_val < target_val)

        logger.warning("Unrecognized operator '%s' in applicability rule; defaulting to True", op)
        return True

    def evaluate_slot(
        self,
        slot: SlotBlueprint,
        regulatory_context: Union[Dict[str, Any], RegulatoryContext],
    ) -> EvaluatedSlot:
        """Evaluates an individual slot's runtime active state and initial status.

        Args:
            slot: SlotBlueprint from form definition.
            regulatory_context: Context dictionary or RegulatoryContext model.

        Returns:
            EvaluatedSlot containing active flag and initial status.
        """
        is_active = self.evaluate_rule(slot.applicability_rule, regulatory_context)

        deactivation_reason = None
        if not is_active:
            status = "NOT_APPLICABLE"
            rule = slot.applicability_rule
            deactivation_reason = f"Deactivated by statutory predicate: {rule.field} {rule.operator} {rule.value}"
        elif slot.is_mandatory:
            status = "MISSING"
        else:
            status = "OPTIONAL"

        return EvaluatedSlot(
            slot_id=slot.slot_id,
            slot_number=slot.slot_number,
            title=slot.title,
            category=slot.category,
            is_mandatory=slot.is_mandatory,
            is_active=is_active,
            status=status,
            deactivation_reason=deactivation_reason,
            slot=slot,
        )

    def evaluate_blueprint_slots(
        self,
        blueprint: FormBlueprint,
        regulatory_context: Union[Dict[str, Any], RegulatoryContext],
    ) -> List[EvaluatedSlot]:
        """Evaluates all discrete slots in a blueprint against regulatory context.

        Args:
            blueprint: FormBlueprint containing discrete upload slots.
            regulatory_context: Submission context dictionary or model.

        Returns:
            List of EvaluatedSlot instances in statutory sequence.
        """
        return [
            self.evaluate_slot(slot, regulatory_context)
            for slot in blueprint.slots
        ]

    def filter_active_slots(
        self,
        blueprint: FormBlueprint,
        regulatory_context: Union[Dict[str, Any], RegulatoryContext],
    ) -> List[SlotBlueprint]:
        """Filters and returns only active SlotBlueprints for a given context.

        Args:
            blueprint: FormBlueprint to filter.
            regulatory_context: Context parameters.

        Returns:
            List of active SlotBlueprint instances.
        """
        return [
            slot for slot in blueprint.slots
            if self.evaluate_rule(slot.applicability_rule, regulatory_context)
        ]


# Default global singleton instance
rules_engine = RulesEngine()
