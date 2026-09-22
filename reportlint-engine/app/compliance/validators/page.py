from app.models.rule_model import Rule
from app.models.result_model import Violation, Location
from app.compliance.validators.base import Validator, within_tolerance


class PageSizeValidator(Validator):
    def validate(self, doc, rule: Rule):
        exp_w = rule.expected_value.get("width_pt")
        exp_h = rule.expected_value.get("height_pt")
        if exp_w is None or exp_h is None or not doc.sections:
            return [], 0
        tol = (rule.tolerance or {}).get("pt", 2.0)
        sec = doc.sections[0]
        checks = 1
        if sec.page_width_pt is None or sec.page_height_pt is None:
            return [], checks
        if not (within_tolerance(sec.page_width_pt, exp_w, tol)
                and within_tolerance(sec.page_height_pt, exp_h, tol)):
            return [Violation(
                rule_id=rule.id, severity=rule.severity, category="PAGE_LAYOUT",
                message=f"Page size expected {exp_w}x{exp_h}pt",
                expected={"width_pt": exp_w, "height_pt": exp_h},
                actual={"width_pt": sec.page_width_pt, "height_pt": sec.page_height_pt},
                location=Location(section="Document"),
            )], checks
        return [], checks


class MarginValidator(Validator):
    def validate(self, doc, rule: Rule):
        if not doc.sections:
            return [], 0
        tol = (rule.tolerance or {}).get("pt", 2.0)
        sec = doc.sections[0]
        mapping = {
            "top": sec.margin_top_pt, "bottom": sec.margin_bottom_pt,
            "left": sec.margin_left_pt, "right": sec.margin_right_pt,
        }
        checks = 0
        violations = []
        for side, expected in rule.expected_value.items():
            actual = mapping.get(side)
            if actual is None:
                continue
            checks += 1
            if not within_tolerance(actual, expected, tol):
                violations.append(Violation(
                    rule_id=rule.id, severity=rule.severity, category="PAGE_LAYOUT",
                    message=f"Margin '{side}' expected {expected}pt, found {actual}pt",
                    expected={side: expected}, actual={side: actual},
                    location=Location(section="Document"),
                ))
        return violations, checks
