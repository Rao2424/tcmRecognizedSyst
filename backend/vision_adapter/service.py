import json
import logging
import re
from dataclasses import dataclass
from typing import Any

import httpx

from .config import settings


NAME_CLEAN_PATTERN = re.compile(r"[\s\-_/\\·,.，。；;:：()（）]+")
logger = logging.getLogger(__name__)


class AdapterConfigError(Exception):
    pass


class ProviderResponseError(Exception):
    pass


@dataclass
class WhitelistItem:
    name: str
    aliases: list[str]


class OpenAICompatibleVisionService:
    async def recognize(
        self,
        *,
        filename: str,
        content_type: str,
        image_base64: str,
        whitelist: list[WhitelistItem],
    ) -> dict[str, Any]:
        self._validate_settings()

        provider_payload = await self._request_provider(
            filename=filename,
            content_type=content_type,
            image_base64=image_base64,
            whitelist=whitelist,
        )
        return self._normalize_model_result(provider_payload, whitelist)

    def _validate_settings(self) -> None:
        if not settings.openai_compatible_base_url:
            raise AdapterConfigError("未配置 OPENAI_COMPATIBLE_BASE_URL")

        if not settings.openai_compatible_api_key:
            raise AdapterConfigError("未配置 OPENAI_COMPATIBLE_API_KEY")

        if not settings.vision_model:
            raise AdapterConfigError("未配置 VISION_MODEL")

    async def _request_provider(
        self,
        *,
        filename: str,
        content_type: str,
        image_base64: str,
        whitelist: list[WhitelistItem],
    ) -> dict[str, Any]:
        whitelist_payload = [
            {"name": item.name, "aliases": item.aliases}
            for item in whitelist
        ]
        data_url = f"data:{content_type or 'image/jpeg'};base64,{image_base64}"
        messages = [
            {
                "role": "system",
                "content": (
                    "你是中药材图片识别服务。"
                    "你必须基于图片内容进行判断，不能依赖文件名、路径、扩展名或其他元数据。"
                    "你只能从给定白名单的标准名中返回结果，绝不能返回白名单外名称。"
                    "如果图片不是单味药材、过度模糊、遮挡严重、无法确认，宁可返回未识别。"
                    "输出必须是 JSON 对象，不要输出 Markdown，不要输出额外解释。"
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "请识别这张中药材图片。\n"
                            f"文件名仅供追踪，不可作为主要识别依据：{filename}\n"
                            f"允许识别的白名单如下：{json.dumps(whitelist_payload, ensure_ascii=False)}\n"
                            "返回 JSON，结构必须为："
                            '{"top1_name": "标准名或null", "top1_confidence": 0到1之间的数字或null, '
                            '"top1_reason": "一句中文理由", "candidates": ['
                            '{"name": "标准名", "confidence": 0到1之间数字, "reason": "一句中文理由"}'
                            "]}。\n"
                            f"candidates 最多返回 {settings.vision_max_candidates} 个，按置信度降序。"
                            "如果无法稳定判断，top1_name 设为 null，candidates 可为空数组。"
                            "返回的 name 必须是白名单中的标准名，不能返回别名。"
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url,
                            "detail": settings.vision_image_detail,
                        },
                    },
                ],
            },
        ]

        payload: dict[str, Any] = {
            "model": settings.vision_model,
            "messages": messages,
            "temperature": settings.vision_temperature,
        }
        if settings.provider_supports_json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {settings.openai_compatible_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=settings.vision_request_timeout) as client:
            logger.info(
                "Calling upstream vision provider: provider=%s, model=%s, url=%s",
                settings.vision_provider_name,
                settings.vision_model,
                settings.chat_completions_url,
            )
            response = await client.post(
                settings.chat_completions_url,
                json=payload,
                headers=headers,
            )

            if response.status_code == 400 and "response_format" in payload:
                payload.pop("response_format", None)
                response = await client.post(
                    settings.chat_completions_url,
                    json=payload,
                    headers=headers,
                )

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ProviderResponseError(
                    f"上游视觉模型请求失败({exc.response.status_code})"
                ) from exc

            try:
                logger.info(
                    "Upstream vision provider responded successfully: status=%s",
                    response.status_code,
                )
                return response.json()
            except ValueError as exc:
                raise ProviderResponseError("上游视觉模型返回了无法解析的 JSON") from exc

    def _normalize_model_result(
        self,
        payload: dict[str, Any],
        whitelist: list[WhitelistItem],
    ) -> dict[str, Any]:
        alias_map = self._build_alias_map(whitelist)
        message_content = self._extract_message_content(payload)
        parsed = self._parse_json_content(message_content)

        raw_top1_name = parsed.get("top1_name")
        raw_top1_confidence = parsed.get("top1_confidence")
        raw_top1_reason = str(parsed.get("top1_reason") or "").strip()

        top1_name = self._normalize_name(raw_top1_name, alias_map)
        top1_confidence = self._clamp_confidence(raw_top1_confidence)
        candidates = self._normalize_candidates(parsed.get("candidates"), alias_map)

        if top1_name is None and candidates:
            top1_name = candidates[0]["name"]
            top1_confidence = candidates[0]["confidence"]
            raw_top1_reason = raw_top1_reason or candidates[0]["reason"]

        if top1_name and top1_confidence is None:
            for item in candidates:
                if item["name"] == top1_name:
                    top1_confidence = item["confidence"]
                    break

        if top1_name is None:
            top1_reason = raw_top1_reason or "模型未能在白名单范围内稳定识别该图片。"
        else:
            top1_reason = raw_top1_reason or "模型根据图片内容给出了白名单范围内的候选结果。"

        return {
            "top1_name": top1_name,
            "top1_confidence": top1_confidence,
            "top1_reason": top1_reason,
            "candidates": candidates[: settings.vision_max_candidates],
        }

    def _extract_message_content(self, payload: dict[str, Any]) -> Any:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderResponseError("上游视觉模型返回结构缺少 choices")

        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise ProviderResponseError("上游视觉模型返回结构缺少 message")

        content = message.get("content")
        if content in (None, ""):
            raise ProviderResponseError("上游视觉模型未返回识别内容")

        return content

    def _parse_json_content(self, content: Any) -> dict[str, Any]:
        if isinstance(content, dict):
            return content

        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict):
                    text_value = item.get("text")
                    if text_value:
                        text_parts.append(str(text_value))
            content = "\n".join(text_parts)

        if not isinstance(content, str):
            raise ProviderResponseError("上游视觉模型返回内容格式异常")

        normalized = content.strip()
        if normalized.startswith("```"):
            normalized = re.sub(r"^```(?:json)?\s*", "", normalized, flags=re.IGNORECASE)
            normalized = re.sub(r"\s*```$", "", normalized)

        try:
            parsed = json.loads(normalized)
            if isinstance(parsed, dict):
                return parsed
        except ValueError:
            pass

        start = normalized.find("{")
        end = normalized.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(normalized[start : end + 1])
                if isinstance(parsed, dict):
                    return parsed
            except ValueError:
                pass

        raise ProviderResponseError("无法从上游视觉模型响应中解析识别 JSON")

    def _build_alias_map(self, whitelist: list[WhitelistItem]) -> dict[str, str]:
        alias_map: dict[str, str] = {}
        for item in whitelist:
            normalized_name = self._normalize_key(item.name)
            if normalized_name:
                alias_map[normalized_name] = item.name

            for alias in item.aliases:
                normalized_alias = self._normalize_key(alias)
                if normalized_alias:
                    alias_map[normalized_alias] = item.name

        return alias_map

    def _normalize_candidates(
        self,
        raw_candidates: Any,
        alias_map: dict[str, str],
    ) -> list[dict[str, Any]]:
        if not isinstance(raw_candidates, list):
            return []

        normalized_candidates: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        for item in raw_candidates:
            if not isinstance(item, dict):
                continue

            normalized_name = self._normalize_name(item.get("name"), alias_map)
            if not normalized_name or normalized_name in seen_names:
                continue

            normalized_candidates.append(
                {
                    "name": normalized_name,
                    "confidence": self._clamp_confidence(
                        item.get("confidence"), default=0.0
                    ),
                    "reason": str(item.get("reason") or "").strip()
                    or "模型给出的候选结果。",
                }
            )
            seen_names.add(normalized_name)

            if len(normalized_candidates) >= settings.vision_max_candidates:
                break

        return normalized_candidates

    def _normalize_name(
        self,
        value: Any,
        alias_map: dict[str, str],
    ) -> str | None:
        normalized_key = self._normalize_key(str(value or ""))
        if not normalized_key:
            return None

        return alias_map.get(normalized_key)

    def _normalize_key(self, value: str) -> str:
        return NAME_CLEAN_PATTERN.sub("", value or "").strip().lower()

    def _clamp_confidence(
        self,
        value: Any,
        default: float | None = None,
    ) -> float | None:
        if value in (None, ""):
            return default

        try:
            return round(max(0.0, min(1.0, float(value))), 4)
        except (TypeError, ValueError):
            return default
