"""
OpenAI provider integration.

Captures: model, prompt, response, input tokens, output tokens, total tokens,
response time. Falls back to a deterministic demo response when no
OPENAI_API_KEY is configured, so the whole system works without paid API keys.
"""
import logging
import random
import time

from config.settings import OPENAI_API_KEY, is_openai_configured

logger = logging.getLogger("openai_provider")


def _demo_response(model: str, prompt: str) -> dict:
    start = time.time()
    time.sleep(0.15)  # simulate network latency for a realistic demo

    demo_text = (
        f"[DEMO RESPONSE - model={model}]\n\n"
        f"This is a simulated OpenAI response for the prompt you submitted. "
        f"In demo mode no real API call is made. Configure OPENAI_API_KEY in .env "
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
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    response_time = round(time.time() - start, 3)

    choice_text = completion.choices[0].message.content
    usage = completion.usage

    return {
        "model": model,
        "response": choice_text,
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
        "total_tokens": usage.total_tokens if usage else 0,
        "response_time": response_time,
        "source": "real",
    }


def call_openai(model: str, prompt: str) -> dict:
    if is_openai_configured():
        try:
            return _real_response(model, prompt)
        except Exception as exc:
            logger.warning("OpenAI real API call failed, falling back to demo mode: %s", exc)
            return _demo_response(model, prompt)
    return _demo_response(model, prompt)
