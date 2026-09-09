# 5. Quantization

## Concept
Quantization compresses the size of an LLM by reducing the precision of its weights (e.g., from FP16 to FP8 or INT4). This drastically reduces VRAM requirements and allows for larger batch sizes or execution on cheaper hardware. 

Supported formats generally include:
- **AWQ / GPTQ:** Post-training quantization methods that pack weights into 4-bit precision while attempting to preserve critical outlier activations.
- **QAT (Quantization-Aware Training):** Baking the precision loss directly into the training loop for maximum accuracy.

## Constraints & Implementation Rules
- **Quality Over VRAM:** Never promote a quantized model *only* because it uses less VRAM. The loss in precision can severely harm complex reasoning, formatting, and alignment.
- **Mandatory Validation:** Any deployment of a quantized artifact must be validated with task-level evaluations, structured output validity (JSON schemas), tool-call accuracy, code-test success, and domain-specific checks.

## Implementation Details
- Model sizes and target `gpu_memory_utilization` parameters are carefully selected in the `tuning_guide`. 
- When leveraging heavily compressed models (e.g., 4-bit AWQ) for orchestration or fast-response tasks, we use the `performance-benchmarking` tools to empirically verify that they can still output valid tool invocations before going to production.
