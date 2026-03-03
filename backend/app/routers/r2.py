from fastapi import APIRouter, Depends

from app.dependencies import require_admin
from app.schemas import SignedDownloadRequest, SignedUrlRequest, SignedUrlResponse
from app.services.r2 import generate_signed_download_url, generate_signed_upload_url

router = APIRouter(prefix='/r2', tags=['r2'], dependencies=[Depends(require_admin)])


@router.post('/upload-url', response_model=SignedUrlResponse)
def upload_url(payload: SignedUrlRequest):
    return SignedUrlResponse(
        object_key=payload.object_key,
        url=generate_signed_upload_url(payload.object_key, payload.mime),
    )


@router.post('/download-url', response_model=SignedUrlResponse)
def download_url(payload: SignedDownloadRequest):
    return SignedUrlResponse(
        object_key=payload.object_key,
        url=generate_signed_download_url(payload.object_key),
    )
