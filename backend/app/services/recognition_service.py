import re
from typing import Any

from sqlalchemy.orm import Session

from ..models.herb import Herb
from .model_client import (
    ModelCandidate,
    ModelClientError,
    VisionModelClient,
)


ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
JPEG_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/pjpeg"}
PNG_CONTENT_TYPES = {"image/png"}
GENERIC_BINARY_CONTENT_TYPES = {"application/octet-stream", "binary/octet-stream"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024
UNRECOGNIZED_NAME = "未识别"
DEFAULT_HERB_WHITELIST: dict[str, list[str]] = {
    "黄芪": ["北芪"],
    "当归": ["秦归"],
    "甘草": ["国老"],
    "桂枝": ["桂尖"],
    "白芍": ["杭芍"],
    "茯苓": ["云苓"],
    "柴胡": ["北柴胡"],
    "人参": ["园参"],
    "生姜": ["鲜姜"],
    "薄荷": ["蕃荷菜"],
}

NAME_SEPARATOR_PATTERN = re.compile(r"[、，,;；/\\\s]+")
NAME_CLEAN_PATTERN = re.compile(r"[\s\-_/\\·,.，。；;:：()（）]+")


class RecognitionServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    return NAME_CLEAN_PATTERN.sub("", value).strip().lower()


def normalize_herb_name(
    name: str | None,
    whitelist: dict[str, list[str]] | None = None,
) -> str | None:
    active_whitelist = whitelist or DEFAULT_HERB_WHITELIST
    normalized_name = _normalize_text(name)
    if not normalized_name:
        return None

    if normalized_name == _normalize_text(UNRECOGNIZED_NAME):
        return None

    for standard_name, aliases in active_whitelist.items():
        if normalized_name == _normalize_text(standard_name):
            return standard_name

        for alias in aliases:
            if normalized_name == _normalize_text(alias):
                return standard_name

    return str(name).strip() or None


def _detect_image_format(image_bytes: bytes) -> str | None:
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "jpeg"

    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"

    return None


def _normalize_content_type(content_type: str) -> str:
    return (content_type or "").split(";", 1)[0].strip().lower()


def _default_content_type_for_format(image_format: str) -> str:
    if image_format == "jpeg":
        return "image/jpeg"

    if image_format == "png":
        return "image/png"

    return ""


def _guess_format_from_metadata(filename: str, content_type: str) -> str | None:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    normalized_content_type = _normalize_content_type(content_type)

    if extension in {"jpg", "jpeg"}:
        if not normalized_content_type or normalized_content_type in GENERIC_BINARY_CONTENT_TYPES:
            return "jpeg"
        if normalized_content_type in JPEG_CONTENT_TYPES:
            return "jpeg"

    if extension == "png":
        if not normalized_content_type or normalized_content_type in GENERIC_BINARY_CONTENT_TYPES:
            return "png"
        if normalized_content_type in PNG_CONTENT_TYPES:
            return "png"

    return None


def _is_extension_compatible(extension: str, detected_format: str) -> bool:
    if not extension:
        return True

    if detected_format == "jpeg":
        return extension in {"jpg", "jpeg"}

    if detected_format == "png":
        return extension == "png"

    return False


def _is_content_type_compatible(content_type: str, detected_format: str) -> bool:
    if not content_type or content_type in GENERIC_BINARY_CONTENT_TYPES:
        return True

    if not content_type.startswith("image/"):
        return False

    if detected_format == "jpeg":
        return content_type in JPEG_CONTENT_TYPES

    if detected_format == "png":
        return content_type in PNG_CONTENT_TYPES

    return True


def validate_image_file(
    *,
    filename: str,
    content_type: str,
    image_bytes: bytes,
) -> str:
    if not image_bytes:
        raise RecognitionServiceError("图片不能为空")

    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise RecognitionServiceError("图片大小不能超过 5MB")

    detected_format = _detect_image_format(image_bytes)
    if detected_format is None:
        detected_format = _guess_format_from_metadata(filename, content_type)

    if detected_format is None:
        raise RecognitionServiceError("上传文件不是有效图片")

    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension and extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise RecognitionServiceError("仅支持 JPG、JPEG、PNG 格式图片")

    if extension and not _is_extension_compatible(extension, detected_format):
        raise RecognitionServiceError("图片扩展名与实际格式不一致")

    normalized_content_type = _normalize_content_type(content_type)
    if not _is_content_type_compatible(normalized_content_type, detected_format):
        raise RecognitionServiceError("上传文件类型与实际图片格式不一致")

    return detected_format


def _split_aliases(alias_text: str | None) -> list[str]:
    if not alias_text:
        return []

    parts = NAME_SEPARATOR_PATTERN.split(alias_text.strip())
    return [item.strip() for item in parts if item.strip()]


def build_herb_whitelist(db: Session) -> dict[str, list[str]]:
    whitelist: dict[str, list[str]] = {}

    for herb in db.query(Herb).order_by(Herb.id.asc()).all():
        name = (herb.name or "").strip()
        if not name:
            continue

        aliases: list[str] = []
        for alias in _split_aliases(herb.alias):
            if alias == name or alias in aliases:
                continue
            aliases.append(alias)

        whitelist[name] = aliases

    return whitelist or DEFAULT_HERB_WHITELIST


def match_herb_by_name_or_alias(
    db: Session,
    name: str | None,
    whitelist: dict[str, list[str]] | None = None,
) -> Herb | None:
    normalized_name = normalize_herb_name(name, whitelist)
    if not normalized_name:
        return None

    herb = db.query(Herb).filter(Herb.name == normalized_name).first()
    if herb:
        return herb

    normalized_target = _normalize_text(normalized_name)
    for item in db.query(Herb).filter(Herb.alias.isnot(None)).all():
        aliases = _split_aliases(item.alias)
        if normalized_target in {_normalize_text(alias) for alias in aliases}:
            return item

        if normalized_target == _normalize_text(item.alias):
            return item

    return None


def _normalize_candidate_list(
    candidates: list[ModelCandidate],
    whitelist: dict[str, list[str]],
) -> list[dict[str, Any]]:
    normalized_candidates: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    for item in candidates:
        normalized_name = normalize_herb_name(item.name, whitelist)
        if not normalized_name or normalized_name not in whitelist:
            continue

        if normalized_name in seen_names:
            continue

        seen_names.add(normalized_name)
        normalized_candidates.append(
            {
                "name": normalized_name,
                "confidence": round(max(0.0, min(1.0, item.confidence)), 4),
                "reason": item.reason,
            }
        )

        if len(normalized_candidates) >= 3:
            break

    return normalized_candidates


def _build_matched_payload(
    *,
    herb: Herb,
    confidence: float | None,
    reason: str,
) -> dict[str, Any]:
    return {
        "herbId": herb.id,
        "name": herb.name,
        "alias": herb.alias,
        "confidence": round(confidence or 0.0, 4),
        "reason": reason,
    }


async def recognize_herb_image(
    *,
    db: Session,
    image_bytes: bytes,
    filename: str,
    content_type: str,
) -> dict[str, Any]:
    herb_whitelist = build_herb_whitelist(db)
    detected_format = validate_image_file(
        filename=filename,
        content_type=content_type,
        image_bytes=image_bytes,
    )
    normalized_filename = (filename or "").strip() or f"upload.{detected_format}"
    normalized_content_type = (
        _normalize_content_type(content_type)
        or _default_content_type_for_format(detected_format)
    )

    client = VisionModelClient()
    try:
        model_result = await client.recognize_herb_image(
            image_bytes=image_bytes,
            filename=normalized_filename,
            content_type=normalized_content_type,
            whitelist=herb_whitelist,
        )
    except ModelClientError as exc:
        raise RecognitionServiceError(str(exc), status_code=502) from exc

    normalized_top1_name = normalize_herb_name(model_result.top1_name, herb_whitelist)
    normalized_candidates = _normalize_candidate_list(
        model_result.candidates,
        herb_whitelist,
    )

    if (
        normalized_top1_name
        and normalized_top1_name in herb_whitelist
        and normalized_top1_name not in {item["name"] for item in normalized_candidates}
    ):
        normalized_candidates.insert(
            0,
            {
                "name": normalized_top1_name,
                "confidence": round(model_result.top1_confidence or 0.0, 4),
                "reason": model_result.top1_reason,
            },
        )

    normalized_candidates = normalized_candidates[:3]

    primary_name = None
    primary_confidence = model_result.top1_confidence
    primary_reason = model_result.top1_reason

    if normalized_top1_name and normalized_top1_name in herb_whitelist:
        primary_name = normalized_top1_name
    elif normalized_candidates:
        primary_name = normalized_candidates[0]["name"]
        primary_confidence = normalized_candidates[0]["confidence"]
        primary_reason = normalized_candidates[0]["reason"]

    matched_herb = match_herb_by_name_or_alias(db, primary_name, herb_whitelist)

    return {
        "recordId": None,
        "matched": (
            _build_matched_payload(
                herb=matched_herb,
                confidence=primary_confidence,
                reason=primary_reason,
            )
            if matched_herb and primary_name
            else None
        ),
        "candidates": normalized_candidates,
        "unmatchedName": None if matched_herb else (primary_name or UNRECOGNIZED_NAME),
    }
