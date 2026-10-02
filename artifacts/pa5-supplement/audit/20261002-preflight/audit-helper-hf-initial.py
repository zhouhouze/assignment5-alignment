"""Capture versions and optional gated-file access without downloading weights."""

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import urllib.error
import urllib.request


def command(args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=15)
        return {"exit_code": result.returncode, "stdout": result.stdout.strip()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"error_type": type(exc).__name__}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check-model-access", action="store_true")
    args = parser.parse_args()
    versions = {}
    for name in ("torch", "transformers", "vllm", "flash-attn", "huggingface-hub", "alpaca-eval"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    info = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "executable": sys.executable,
        "packages": versions,
        "git_commit": command(["git", "rev-parse", "HEAD"]),
        "git_status": command(["git", "status", "--short", "--branch"]),
        "gpu": command(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,driver_version", "--format=csv,noheader"]),
        "disk": command(["df", "-h", "."]),
        "model_access": [],
    }
    if args.check_model_access:
        hf_home = Path(os.getenv("HF_HOME", str(Path.home() / ".cache/huggingface")))
        token_path = Path(os.getenv("HF_TOKEN_PATH", str(hf_home / "token")))
        token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
        if not token and token_path.is_file():
            token = token_path.read_text().strip()
        info["hf_credential_present"] = bool(token)
        for model, revision in (
            ("meta-llama/Meta-Llama-3.1-8B", "d04e592bb4f6aa9cfee91e2e20afa771667e1d4b"),
            ("meta-llama/Llama-3.3-70B-Instruct", "6f6073b423013f6a7d4d9f39144961bfbfbc386b"),
        ):
            item = {"model_id": model, "revision": revision, "files": {}}
            for filename in ("config.json", "tokenizer_config.json"):
                request = urllib.request.Request(
                    f"https://huggingface.co/{model}/resolve/{revision}/{filename}",
                    method="HEAD",
                    headers={"Authorization": f"Bearer {token}"} if token else {},
                )
                try:
                    with urllib.request.urlopen(request, timeout=15) as response:
                        item["files"][filename] = {"http_status": response.status}
                except urllib.error.HTTPError as exc:
                    item["files"][filename] = {"http_status": exc.code}
                except (OSError, urllib.error.URLError) as exc:
                    item["files"][filename] = {"error_type": type(exc).__name__}
            info["model_access"].append(item)
    # Never overwrite a previous audit or emit credentials into the report.
    with args.output.open("x") as output:
        json.dump(info, output, indent=2)
        output.write("\n")
    print(f"Audit saved to {args.output}")


if __name__ == "__main__":
    main()
