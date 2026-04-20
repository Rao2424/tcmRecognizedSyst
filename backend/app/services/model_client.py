import base64
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from ..core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class ModelCandidate:
    name: str
    confidence: float
    reason: str


@dataclass
class ModelRecognitionResult:
    top1_name: str | None
    top1_confidence: float | None
    top1_reason: str
    candidates: list[ModelCandidate]


class ModelClientError(Exception):
    pass


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _extract_result_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ModelClientError("视觉识别服务返回结构异常")

    if isinstance(payload.get("data"), dict):
        return payload["data"]

    if isinstance(payload.get("result"), dict):
        return payload["result"]

    return payload


def _parse_candidates(raw_candidates: Any) -> list[ModelCandidate]:
    if not isinstance(raw_candidates, list):
        return []

    candidates: list[ModelCandidate] = []
    for item in raw_candidates:
        if not isinstance(item, dict):
            continue

        name = str(item.get("name") or "").strip()
        if not name:
            continue

        candidates.append(
            ModelCandidate(
                name=name,
                confidence=max(0.0, min(1.0, _coerce_float(item.get("confidence")))),
                reason=str(item.get("reason") or "").strip(),
            )
        )

    return candidates


def _parse_result(payload: Any) -> ModelRecognitionResult:
    result = _extract_result_payload(payload)
    candidates = _parse_candidates(result.get("candidates"))
    top1_name = str(result.get("top1_name") or "").strip() or None
    top1_confidence_raw = result.get("top1_confidence")
    top1_reason = str(result.get("top1_reason") or "").strip()

    if top1_name is None and candidates:
        top1_name = candidates[0].name
        top1_confidence = candidates[0].confidence
        top1_reason = top1_reason or candidates[0].reason
    else:
        top1_confidence = None
        if top1_confidence_raw is not None:
            top1_confidence = max(
                0.0,
                min(1.0, _coerce_float(top1_confidence_raw)),
            )

    return ModelRecognitionResult(
        top1_name=top1_name,
        top1_confidence=top1_confidence,
        top1_reason=top1_reason,
        candidates=candidates,
    )


def _normalize_filename_for_fallback(filename: str) -> str:
    stem = Path(filename or "").stem.strip().lower()
    return "".join(ch for ch in stem if ch.isalnum() or ("\u4e00" <= ch <= "\u9fff"))


class VisionModelClient:
    async def recognize_herb_image(
        self,
        *,
        image_bytes: bytes,
        filename: str,
        content_type: str,
        whitelist: dict[str, list[str]],
    ) -> ModelRecognitionResult:
        if settings.vision_api_url:
            logger.info(
                "Recognition is using remote vision adapter: url=%s, filename=%s",
                settings.vision_api_url,
                filename,
            )
            return await self._call_remote_model(
                image_bytes=image_bytes,
                filename=filename,
                content_type=content_type,
                whitelist=whitelist,
            )

        logger.info(
            "Recognition is using local filename fallback: filename=%s",
            filename,
        )
        return self._fallback_from_filename(filename=filename, whitelist=whitelist)

    async def _call_remote_model(
        self,
        *,
        image_bytes: bytes,
        filename: str,
        content_type: str,
        whitelist: dict[str, list[str]],
    ) -> ModelRecognitionResult:
        headers: dict[str, str] = {}
        if settings.vision_api_key:
            headers["Authorization"] = f"Bearer {settings.vision_api_key}"

        payload = {
            "filename": filename,
            "content_type": content_type,
            "image_base64": base64.b64encode(image_bytes).decode("utf-8"),
            "whitelist": [
                {"name": name, "aliases": aliases}
                for name, aliases in whitelist.items()
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=settings.vision_api_timeout) as client:
                logger.info(
                    "Calling vision adapter: url=%s, whitelist_count=%s",
                    settings.vision_api_url,
                    len(whitelist),
                )
                response = await client.post(
                    settings.vision_api_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                logger.info(
                    "Vision adapter responded successfully: status=%s",
                    response.status_code,
                )
        except httpx.TimeoutException as exc:
            raise ModelClientError("视觉识别服务超时") from exc
        except httpx.HTTPStatusError as exc:
            raise ModelClientError(
                f"视觉识别服务请求失败({exc.response.status_code})"
            ) from exc
        except httpx.HTTPError as exc:
            raise ModelClientError("视觉识别服务连接失败") from exc
        except ValueError as exc:
            raise ModelClientError("视觉识别服务返回了无法解析的结果") from exc

        return _parse_result(data)

    def _fallback_from_filename(
        self,
        *,
        filename: str,
        whitelist: dict[str, list[str]],
    ) -> ModelRecognitionResult:
        normalized_filename = _normalize_filename_for_fallback(filename)

        for standard_name, aliases in whitelist.items():
            names = [standard_name, *aliases]
            for candidate_name in names:
                normalized_candidate = _normalize_filename_for_fallback(candidate_name)
                if normalized_candidate and normalized_candidate in normalized_filename:
                    candidate_pool = [standard_name]
                    candidate_pool.extend(
                        other_name
                        for other_name in whitelist.keys()
                        if other_name != standard_name
                    )
                    top_candidates = candidate_pool[:3]
                    return ModelRecognitionResult(
                        top1_name=standard_name,
                        top1_confidence=0.92,
                        top1_reason="当前未配置 VISION_API_URL，已按文件名命中白名单关键词执行本地降级识别。",
                        candidates=[
                            ModelCandidate(
                                name=top_candidates[0],
                                confidence=0.92,
                                reason="文件名与白名单药材名称或别名一致。",
                            ),
                            ModelCandidate(
                                name=top_candidates[1],
                                confidence=0.24,
                                reason="本地降级模式下提供的候选参考项。",
                            ),
                            ModelCandidate(
                                name=top_candidates[2],
                                confidence=0.13,
                                reason="本地降级模式下提供的候选参考项。",
                            ),
                        ],
                    )

        return ModelRecognitionResult(
            top1_name=None,
            top1_confidence=None,
            top1_reason="当前未配置 VISION_API_URL，系统只会按文件名执行降级匹配；随机拍照文件名通常无法命中白名单关键词。",
            candidates=[],
        )
