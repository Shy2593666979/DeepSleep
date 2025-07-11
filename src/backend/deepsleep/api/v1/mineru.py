from fastapi import APIRouter, UploadFile, Form, File, Depends

from deepsleep.api.services.user import UserPayload, get_login_user
from deepsleep.schema.schemas import UnifiedResponseModel

router = APIRouter

@router.post("/doc_parse", response_model=UnifiedResponseModel)
async def doc_parse(file: UploadFile = File(...),
                    knowledge_id: str = Form(...),
                    output_dir: str = Form(...),
                    login_user: UserPayload = Depends(get_login_user)):
    pass