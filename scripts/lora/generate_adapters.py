"""Generate valid local PEFT LoRA adapters for Multi-LoRA serving in vLLM.

Uses only Python standard library (no external dependencies required).
Generates compliant adapter_config.json and adapter_model.safetensors for offline
testing or continuous integration without requiring Hugging Face downloads.
"""

import json
import os
import pathlib
import struct


def write_safetensors_file(file_path: str, tensors_dict: dict[str, tuple[list[int], bytes]]):
    """Write raw tensors into a valid .safetensors binary file."""
    header = {}
    current_offset = 0
    raw_buffer = bytearray()

    for name, (shape, data_bytes) in tensors_dict.items():
        data_len = len(data_bytes)
        header[name] = {
            "dtype": "BF16",
            "shape": shape,
            "data_offsets": [current_offset, current_offset + data_len],
        }
        raw_buffer.extend(data_bytes)
        current_offset += data_len

    header_json = json.dumps(header).encode("utf-8")
    header_len = len(header_json)

    with open(file_path, "wb") as f:
        # 8 bytes unsigned 64-bit little endian length
        f.write(struct.pack("<Q", header_len))
        f.write(header_json)
        f.write(raw_buffer)


def create_lora_adapter(adapter_dir: str, base_model: str = "Qwen/Qwen2.5-0.5B-Instruct"):
    """Create adapter_config.json and adapter_model.safetensors for a 24-layer Qwen model."""
    os.makedirs(adapter_dir, exist_ok=True)

    # 1. PEFT config
    config = {
        "base_model_name_or_path": base_model,
        "bias": "none",
        "fan_in_fan_out": False,
        "inference_mode": True,
        "init_lora_weights": True,
        "layers_pattern": None,
        "layers_to_transform": None,
        "lora_alpha": 16,
        "lora_dropout": 0.05,
        "modules_to_save": None,
        "peft_type": "LORA",
        "r": 8,
        "target_modules": ["q_proj", "v_proj"],
        "task_type": "CAUSAL_LM",
    }

    with open(os.path.join(adapter_dir, "adapter_config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    # 2. Safetensors binary tensors (Rank 8 BF16 zero weights for non-intrusive baseline activation)
    tensors = {}
    # For Qwen2.5-0.5B: 24 layers, hidden_size=896, v_proj_size=128
    for layer in range(24):
        shape_qa = [8, 896]
        bytes_qa = b"\x00" * (8 * 896 * 2)
        tensors[f"base_model.model.model.layers.{layer}.self_attn.q_proj.lora_A.weight"] = (
            shape_qa,
            bytes_qa,
        )

        shape_qb = [896, 8]
        bytes_qb = b"\x00" * (896 * 8 * 2)
        tensors[f"base_model.model.model.layers.{layer}.self_attn.q_proj.lora_B.weight"] = (
            shape_qb,
            bytes_qb,
        )

        shape_va = [8, 896]
        bytes_va = b"\x00" * (8 * 896 * 2)
        tensors[f"base_model.model.model.layers.{layer}.self_attn.v_proj.lora_A.weight"] = (
            shape_va,
            bytes_va,
        )

        shape_vb = [128, 8]
        bytes_vb = b"\x00" * (128 * 8 * 2)
        tensors[f"base_model.model.model.layers.{layer}.self_attn.v_proj.lora_B.weight"] = (
            shape_vb,
            bytes_vb,
        )

    write_safetensors_file(os.path.join(adapter_dir, "adapter_model.safetensors"), tensors)
    print(f"[OK] Generated PEFT LoRA adapter: {os.path.basename(adapter_dir)}")


def main():
    root_dir = pathlib.Path(__file__).resolve().parents[2]
    adapters_dir = root_dir / "lora_adapters"

    create_lora_adapter(str(adapters_dir / "reasoning-lora"))
    create_lora_adapter(str(adapters_dir / "reflection-lora"))
    print(
        "[SUCCESS] Both reasoning-lora and reflection-lora adapters are ready for vLLM Multi-LoRA serving!"
    )


if __name__ == "__main__":
    main()
