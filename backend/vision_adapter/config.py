import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
_EXISTING_ENV_KEYS = set(os.environ.keys())


def _load_env_file(env_path: Path, *, override_loaded_values: bool) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        normalized_key = key.strip()
        normalized_value = value.strip()

        if normalized_key in _EXISTING_ENV_KEYS:
            continue

        if override_loaded_values or normalized_key not in os.environ:
            os.environ[normalized_key] = normalized_value


_load_env_file(BASE_DIR / ".env", override_loaded_values=False)
_load_env_file(BASE_DIR / ".env.vision", override_loaded_values=True)


def _as_float(value: str, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class Settings:
    service_name: str = os.getenv("VISION_ADAPTER_NAME", "TCM Vision Adapter")
    openai_compatible_base_url: str = (
        os.getenv("OPENAI_COMPATIBLE_BASE_URL", "").strip().rstrip("/")
    )
    openai_compatible_api_key: str = os.getenv(
        "OPENAI_COMPATIBLE_API_KEY", ""
    ).strip()
    vision_model: str = os.getenv("VISION_MODEL", "").strip()
    vision_provider_name: str = os.getenv(
        "VISION_PROVIDER_NAME", "OpenAI-compatible provider"
    ).strip()
    adapter_api_key: str = os.getenv("ADAPTER_API_KEY", "").strip()
    vision_request_timeout: float = _as_float(
        os.getenv("VISION_REQUEST_TIMEOUT", "60"), default=60.0
    )
    vision_temperature: float = _as_float(
        os.getenv("VISION_TEMPERATURE", "0.1"), default=0.1
    )
    vision_max_candidates: int = max(
        1, min(5, _as_int(os.getenv("VISION_MAX_CANDIDATES", "3"), default=3))
    )
    vision_image_detail: str = (
        os.getenv("VISION_IMAGE_DETAIL", "high").strip().lower() or "high"
    )
    provider_supports_json_mode: bool = (
        os.getenv("VISION_JSON_MODE", "true").strip().lower() in {"1", "true", "yes", "on"}
    )

    @property
    def chat_completions_url(self) -> str:
        if self.openai_compatible_base_url.endswith("/chat/completions"):
            return self.openai_compatible_base_url

        return f"{self.openai_compatible_base_url}/chat/completions"


settings = Settings()

