import logging
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .config import settings
from .service import (
    AdapterConfigError,
    OpenAICompatibleVisionService,
    ProviderResponseError,
    WhitelistItem,
)


logger = logging.getLogger(__name__)


class WhitelistItemPayload(BaseModel):
    name: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)


class RecognitionRequest(BaseModel):
    filename: str = ""
    content_type: str = ""
    image_base64: str = Field(min_length=1)
    whitelist: list[WhitelistItemPayload] = Field(min_length=1)


async def verify_adapter_token(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    if not settings.adapter_api_key:
        return

    expected = f"Bearer {settings.adapter_api_key}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


app = FastAPI(title=settings.service_name, version="0.1.0")


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": f"{settings.service_name} is running.",
        "provider": settings.vision_provider_name,
    }


@app.get("/health")
def health_check() -> dict[str, bool | str]:
    return {
        "status": "ok",
        "provider": settings.vision_provider_name,
        "configured": bool(
            settings.openai_compatible_base_url
            and settings.openai_compatible_api_key
            and settings.vision_model
        ),
    }


@app.post("/recognize")
async def recognize_image(
    payload: RecognitionRequest,
    _: None = Depends(verify_adapter_token),
) -> dict:
    service = OpenAICompatibleVisionService()
    logger.info(
        "Vision adapter received recognize request: filename=%s, whitelist_count=%s",
        payload.filename,
        len(payload.whitelist),
    )

    try:
        result = await service.recognize(
            filename=payload.filename,
            content_type=payload.content_type,
            image_base64=payload.image_base64,
            whitelist=[
                WhitelistItem(name=item.name, aliases=item.aliases)
                for item in payload.whitelist
            ],
        )
        logger.info(
            "Vision adapter completed request: top1_name=%s",
            result.get("top1_name"),
        )
        return result
    except AdapterConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ProviderResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="上游视觉模型请求超时") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="上游视觉模型连接失败") from exc
