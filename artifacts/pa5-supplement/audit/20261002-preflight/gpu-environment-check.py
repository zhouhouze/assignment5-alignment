"""Environment-only CUDA/FA2 validation; no model weights or generation."""
import contextlib
import json
import sys
import traceback

result = {"kind": "environment_check", "model_loaded": False}
try:
    with contextlib.redirect_stdout(sys.stderr):
        import torch
        import transformers
        import vllm
        import flash_attn
        from flash_attn import flash_attn_func

        torch.manual_seed(0)
        result.update(
            torch=torch.__version__,
            cuda_runtime=torch.version.cuda,
            transformers=transformers.__version__,
            vllm=vllm.__version__,
            flash_attn=flash_attn.__version__,
            cuda_available=torch.cuda.is_available(),
            gpu_count=torch.cuda.device_count(),
        )
        assert result["cuda_available"]
        x = torch.randn(32, 32, device="cuda", dtype=torch.bfloat16)
        y = x @ x
        result["bf16_matmul_finite"] = bool(torch.isfinite(y).all().item())
        q = torch.randn(1, 16, 2, 64, device="cuda", dtype=torch.bfloat16)
        z = flash_attn_func(q, q, q, causal=True)
        torch.cuda.synchronize()
        result["flash_attention_shape"] = list(z.shape)
        result["flash_attention_finite"] = bool(torch.isfinite(z).all().item())
        assert result["bf16_matmul_finite"] and result["flash_attention_finite"]
        assert z.shape == q.shape
        result["passed"] = True
except Exception as exc:
    traceback.print_exc(file=sys.stderr)
    result.update(passed=False, error_type=type(exc).__name__, error=str(exc))
print(json.dumps(result, indent=2))
sys.exit(0 if result["passed"] else 1)
