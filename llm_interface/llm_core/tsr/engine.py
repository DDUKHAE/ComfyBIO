from __future__ import annotations

from .schema import DomainTSR, ToolChoice, ToolValidity

_SAFE_BUILTINS: dict = {}


class TSREngine:
    def __init__(self, tsr: DomainTSR) -> None:
        self._tsr = tsr

    def resolve(self, step_id: str, context: dict) -> list[ToolChoice]:
        result: list[ToolChoice] = []
        for rule in self._tsr.steps:
            if rule.step_id == step_id and self._eval(rule.condition, context):
                result.extend(rule.tools)
        return result

    def canonical(self, step_id: str, context: dict) -> str | None:
        for tc in self.resolve(step_id, context):
            if tc.validity == ToolValidity.CANONICAL:
                return tc.tool_id
        return None

    def is_valid(self, step_id: str, tool_id: str, context: dict) -> ToolValidity:
        for tc in self.resolve(step_id, context):
            if tc.tool_id == tool_id:
                return tc.validity
        return ToolValidity.INVALID

    def _eval(self, condition: str, context: dict) -> bool:
        try:
            return bool(eval(condition, {"__builtins__": _SAFE_BUILTINS}, context))  # noqa: S307
        except Exception:
            return False
