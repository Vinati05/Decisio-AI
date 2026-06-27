from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional

import ollama
from pydantic import BaseModel

class LLMResponse(BaseModel):
    analysis: str
    opportunities: list[str]
    risks: list[str]
    missing_information: list[str]
    suggested_actions: list[Dict[str, Any]]

class OllamaClient:
    """Wrapper for Ollama with fallback support."""
    
    def __init__(self, model: str = "llama3.2", host: Optional[str] = None):
        self.model = model
        self.host = host or os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
        self.client = ollama.Client(host=self.host)
        self.last_error: Optional[str] = None

    def health_check(self) -> Dict[str, Any]:
        """Verify Ollama connectivity and whether the configured model is visible."""
        try:
            models_response = self.client.list()
            models = self._extract_model_names(models_response)
            model_available = self.model in models or any(
                name.startswith(f"{self.model}:") for name in models
            )
            self.last_error = None
            print(
                f"[Ollama] Health check success host={self.host} "
                f"model={self.model} model_available={model_available}"
            )
            return {
                "ok": True,
                "host": self.host,
                "model": self.model,
                "model_available": model_available,
                "models": models,
                "error": None,
            }
        except Exception as exc:
            self.last_error = str(exc)
            print(f"[Ollama] Connection failed host={self.host} model={self.model}: {exc}")
            return {
                "ok": False,
                "host": self.host,
                "model": self.model,
                "model_available": False,
                "models": [],
                "error": str(exc),
            }

    def generate(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """Generate text. Returns None on failure to trigger fallback."""
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": temperature, "num_ctx": 8192}
            )
            content = response["message"]["content"].strip()
            self.last_error = None
            print(f"[Ollama] Success model={self.model} mode=text chars={len(content)}")
            return content
        except Exception as exc:
            self.last_error = str(exc)
            print(f"[Ollama] Generation failed host={self.host} model={self.model}: {exc}")
            return None

    def structured_generate(self, system_prompt: str, user_prompt: str) -> Optional[Dict]:
        """Generate JSON using Ollama JSON mode with tolerant parsing fallback."""
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                format="json",
                options={"temperature": 0.2, "num_ctx": 8192}
            )
            content = response["message"]["content"].strip()
            parsed = self._parse_json_content(content)
            self.last_error = None
            print(
                f"[Ollama] Success model={self.model} mode=json "
                f"chars={len(content)} keys={list(parsed.keys())}"
            )
            return parsed
        except json.JSONDecodeError as exc:
            self.last_error = f"JSON parse error: {exc}"
            print(f"[Ollama] JSON parse failed model={self.model}: {exc}")
            return None
        except Exception as exc:
            self.last_error = str(exc)
            print(f"[Ollama] Structured generation failed host={self.host} model={self.model}: {exc}")
            return None

    @staticmethod
    def _parse_json_content(content: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                raise
            parsed = json.loads(json_match.group(0))

        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list):
            return {"items": parsed}
        return {"value": parsed}

    @staticmethod
    def _extract_model_names(models_response: Any) -> list[str]:
        raw_models = []
        if isinstance(models_response, dict):
            raw_models = models_response.get("models", [])
        else:
            raw_models = getattr(models_response, "models", [])

        names: list[str] = []
        for model in raw_models:
            if isinstance(model, dict):
                name = model.get("name") or model.get("model")
            else:
                name = getattr(model, "name", None) or getattr(model, "model", None)
            if name:
                names.append(str(name))
        return names
