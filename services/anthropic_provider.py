"""
Anthropic Claude provider integration.

Captures: model, prompt, response, input tokens, output tokens, total tokens,
response time. Falls back to a deterministic demo response when no
ANTHROPIC_API_KEY is configured, so the whole system works without paid API keys.
"""
import logging
import random
import time

from config.settings import ANTHROPIC_API_KEY, is_anthropic_configured

logger = logging.getLogger("anthropic_provider")


def _demo_response(model: str, prompt: str) -> dict:
    start = time.time()
    time.sleep(0.15)  # simulate network latency for a realistic demo

    demo_text = (
        f"[DEMO RESPONSE - model={model}]\n\n"
        f"This is a simulated Claude response for the prompt you submitted. "
        f"In demo mode no real API call is made. Configure ANTHROPIC_API_KEY in .env "
        f"to receive real completions.\n\nPrompt received ({len(prompt.split())} words)."
    )

    input_tokens = max(1, int(len(prompt.split()) * 1.3))
    output_tokens = random.randint(60, 220)
    total_tokens = input_tokens + output_tokens
    response_time = round(time.time() - start, 3)

    return {
        "model": model,
        "response": demo_text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "response_time": response_time,
        "source": "demo",
    }


def _real_response(model: str, prompt: str) -> dict:
    start = time.time()
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    response_time = round(time.time() - start, 3)

    response_text = "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    )
    input_tokens = message.usage.input_tokens if message.usage else 0
    output_tokens = message.usage.output_tokens if message.usage else 0

    return {
        "model": model,
        "response": response_text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "response_time": response_time,
        "source": "real",
    }


def call_anthropic(model: str, prompt: str) -> dict:
    if is_anthropic_configured():
        try:
            return _real_response(model, prompt)
        except Exception as exc:
            logger.warning("Anthropic real API call failed, falling back to demo mode: %s", exc)
            return _demo_response(model, prompt)
    return _demo_response(model, prompt)
