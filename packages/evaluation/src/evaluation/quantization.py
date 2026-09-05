from pydantic import BaseModel


class EvaluationResult(BaseModel):
    model_name: str
    quantization_type: str
    pass_rate: float
    latency_p50: float
    ttft_p50: float
    notes: str = ""


class QuantizationEvaluator:
    """
    Scaffold for running regression and quality checks on quantized models.
    Aggressively quantized models (e.g. 4-bit AWQ) can lose the ability to
    output valid JSON or follow strict tool schemas. This suite validates them.
    """

    def __init__(self):
        self.results: list[EvaluationResult] = []

    def evaluate_json_schema_following(self, endpoint: str, model: str) -> float:
        """
        Runs N requests demanding strict JSON output.
        Returns the pass rate (0.0 to 1.0).
        """
        # TODO: Implement actual HTTP calls to the gateway
        return 1.0

    def evaluate_tool_calling(self, endpoint: str, model: str) -> float:
        """
        Runs N requests demanding complex tool usage.
        Returns the pass rate (0.0 to 1.0).
        """
        # TODO: Implement actual HTTP calls to the gateway
        return 1.0
