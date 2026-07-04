#!/usr/bin/env python3
"""Two-stage DeepSeek pipeline for protocol extraction from paper markdown."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib import error, request


DEFAULT_BASE_URL = "https://api.deepseek.com/chat/completions"


def parse_args() -> argparse.Namespace:
    dataset_dir = Path(__file__).resolve().parent.parent / "dataset"
    parser = argparse.ArgumentParser(
        description="Extract preparation evidence and generate protocol JSON with DeepSeek."
    )
    parser.add_argument(
        "markdown",
        help="Path to the source markdown paper.",
    )
    parser.add_argument(
        "--config",
        default=str(Path(__file__).with_name("deepseek_protocol_config.json")),
        help="Path to a JSON config file containing API key and model names.",
    )
    parser.add_argument(
        "--shot-protocol",
        default=str(dataset_dir / "ODMA_GelMA_RSF_CHI_protocol.json"),
        help="Path to the protocol JSON used as a format shot.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(dataset_dir / "output"),
        help="Directory used to save intermediate artifacts.",
    )
    parser.add_argument(
        "--flash-prompt",
        default=str(Path(__file__).with_name("prompts") / "stage1_extract_preparation_evidence.txt"),
        help="Path to the stage-1 prompt template.",
    )
    parser.add_argument(
        "--pro-prompt",
        default=str(Path(__file__).with_name("prompts") / "stage2_generate_protocol.txt"),
        help="Path to the stage-2 prompt template.",
    )
    return parser.parse_args()


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def read_json(path: str) -> dict[str, Any]:
    return json.loads(read_text(path))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, content: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")


def slugify_name(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return slug or "protocol"


def load_config(path: str) -> dict[str, Any]:
    config = read_json(path)
    required_keys = ["api_key", "flash_model", "pro_model"]
    missing = [key for key in required_keys if not config.get(key)]
    if missing:
        raise ValueError(
            "Missing required config keys: " + ", ".join(missing)
        )
    if config["api_key"].startswith("YOUR_"):
        raise ValueError("Please fill in your real DeepSeek API key in the config file.")
    config.setdefault("base_url", DEFAULT_BASE_URL)
    config.setdefault("temperature_flash", 0.1)
    config.setdefault("temperature_pro", 0.0)
    config.setdefault("max_tokens_flash", 65536)
    config.setdefault("max_tokens_pro", 65536)
    return config


def strip_code_fence(text: str) -> str:
    fenced = re.match(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", text, flags=re.DOTALL)
    return fenced.group(1).strip() if fenced else text.strip()


def parse_json_response(text: str) -> Any:
    cleaned = strip_code_fence(text)
    return json.loads(cleaned)


def render_template(template_text: str, replacements: dict[str, str]) -> str:
    rendered = template_text
    for key, value in replacements.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def chat_completion(
    *,
    api_key: str,
    base_url: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        base_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"DeepSeek API request failed: {exc}") from exc

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected DeepSeek API response: {json.dumps(data, ensure_ascii=False)}") from exc


def derive_output_stem(markdown_path: str) -> str:
    return f"{Path(markdown_path).stem}_protocol"


def unique_output_path(directory: Path, base_name: str) -> Path:
    candidate = directory / f"{slugify_name(base_name)}.json"
    if not candidate.exists():
        return candidate
    index = 1
    while True:
        candidate = directory / f"{slugify_name(base_name)}_generated_{index}.json"
        if not candidate.exists():
            return candidate
        index += 1


def main() -> int:
    args = parse_args()
    config = load_config(args.config)

    markdown_path = Path(args.markdown)
    shot_protocol_path = Path(args.shot_protocol)
    output_dir = Path(args.output_dir)
    final_dir = Path(__file__).resolve().parent.parent / "dataset"

    markdown_text = read_text(str(markdown_path))
    shot_protocol = read_json(str(shot_protocol_path))
    shot_protocol_text = json.dumps(shot_protocol, ensure_ascii=False, indent=2)
    output_stem = slugify_name(derive_output_stem(str(markdown_path)))

    stage1_template = read_text(args.flash_prompt)
    stage2_template = read_text(args.pro_prompt)

    stage1_prompt = render_template(
        stage1_template,
        {
            "MARKDOWN_FILE_NAME": markdown_path.name,
            "MARKDOWN_TEXT": markdown_text,
        },
    )

    stage1_system = (
        "You extract preparation evidence from scientific papers. "
        "Return only valid JSON and never add information not present in the source."
    )
    stage1_raw = chat_completion(
        api_key=config["api_key"],
        base_url=config["base_url"],
        model=config["flash_model"],
        system_prompt=stage1_system,
        user_prompt=stage1_prompt,
        temperature=float(config["temperature_flash"]),
        max_tokens=int(config["max_tokens_flash"]),
    )

    write_text(output_dir / f"{output_stem}_stage1_prompt.txt", stage1_prompt)
    write_text(output_dir / f"{output_stem}_stage1_raw_response.txt", stage1_raw)
    stage1_json = parse_json_response(stage1_raw)
    write_json(output_dir / f"{output_stem}_stage1_segments.json", stage1_json)

    stage2_prompt = render_template(
        stage2_template,
        {
            "MARKDOWN_FILE_NAME": markdown_path.name,
            "SHOT_PROTOCOL_JSON": shot_protocol_text,
            "EXTRACTED_SEGMENTS_JSON": json.dumps(stage1_json, ensure_ascii=False, indent=2),
        },
    )

    stage2_system = (
        "You convert extracted preparation evidence into a protocol JSON. "
        "Return only valid JSON, keep chronological consistency, and never hallucinate missing values."
    )
    stage2_raw = chat_completion(
        api_key=config["api_key"],
        base_url=config["base_url"],
        model=config["pro_model"],
        system_prompt=stage2_system,
        user_prompt=stage2_prompt,
        temperature=float(config["temperature_pro"]),
        max_tokens=int(config["max_tokens_pro"]),
    )

    write_text(output_dir / f"{output_stem}_stage2_prompt.txt", stage2_prompt)
    write_text(output_dir / f"{output_stem}_stage2_raw_response.txt", stage2_raw)
    final_protocol = parse_json_response(stage2_raw)
    final_protocol_name = str(final_protocol.get("Protocol", output_stem))
    final_protocol_path = unique_output_path(final_dir, final_protocol_name)
    write_json(final_protocol_path, final_protocol)

    print(f"Stage 1 segments saved to: {output_dir / f'{output_stem}_stage1_segments.json'}")
    print(f"Final protocol saved to: {final_protocol_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
