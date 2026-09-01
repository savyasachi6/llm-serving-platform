"""Download real fine-tuned LoRA adapter checkpoints from Hugging Face Hub.
"""
import os
import urllib.request


def download_file(url: str, dest_path: str):
    file_name = os.path.basename(dest_path)
    print(f"Downloading: {url} -> {file_name}")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req) as response, open(dest_path, "wb") as out_file:
        out_file.write(response.read())
    print(f"[OK] Downloaded {file_name} ({os.path.getsize(dest_path)} bytes)")

def download_hf_lora(repo_id: str, local_dir: str):
    files = ["adapter_config.json", "adapter_model.safetensors"]
    base_url = f"https://huggingface.co/{repo_id}/resolve/main"
    for file_name in files:
        url = f"{base_url}/{file_name}"
        dest = os.path.join(local_dir, file_name)
        download_file(url, dest)

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    adapters_dir = os.path.join(root_dir, "lora_adapters")
    
    # 1. Real fine-tuned reasoning LoRA
    print("\n--- Downloading Real Fine-Tuned Reasoning LoRA ---")
    download_hf_lora(
        "wuyanzu4692/task-13-Qwen-Qwen2.5-0.5B-Instruct",
        os.path.join(adapters_dir, "reasoning-lora")
    )
    
    # 2. Real fine-tuned reflection / bias LoRA
    print("\n--- Downloading Real Fine-Tuned Reflection LoRA ---")
    download_hf_lora(
        "Hebisuke/Qwen2.5-0.5B-Instruct_bias2_0.5B",
        os.path.join(adapters_dir, "reflection-lora")
    )
    
    print("\n[SUCCESS] Both genuine fine-tuned LoRA adapters downloaded from Hugging Face Hub!")

if __name__ == "__main__":
    main()
