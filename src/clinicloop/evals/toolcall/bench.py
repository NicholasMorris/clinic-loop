"""Benchmark utilities: measure tokens per second."""

import json
import time
import urllib.request


def measure_tokens_per_second(
    model_id: str,
    prompt: str,
    base_url: str = "http://localhost:1234/v1",
    max_tokens: int = 500,
) -> float:
    """Measure tokens per second for a model on a given prompt.

    Args:
        model_id: The model identifier.
        prompt: The prompt to measure.
        base_url: Base URL for the LM Studio API.
        max_tokens: Maximum tokens to generate.

    Returns:
        Tokens per second (completion tokens / wall time in seconds).

    Raises:
        RuntimeError: If the model API call fails.
    """
    url = f"{base_url}/chat/completions"

    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=120) as response:
            elapsed = time.time() - start_time
            result = json.loads(response.read())

            # Extract completion tokens from usage
            completion_tokens = result.get("usage", {}).get("completion_tokens", 0)
            if completion_tokens == 0:
                # Fallback: return 0 if no tokens were generated
                return 0.0

            tokens_per_second: float = completion_tokens / elapsed
            return tokens_per_second
    except Exception as e:
        raise RuntimeError(f"Failed to measure tokens/sec for {model_id}: {e}") from e
