from fastapi import APIRouter
from fastapi import Depends

from univy.auth.security import get_current_user
from univy.smart_notes.util import read_json_content


router = APIRouter(prefix="/smart-notes", tags=["smart-notes"])


@router.get("/read-json-content")
async def read_json_content(json_file_name: str, current_user=Depends(get_current_user)):
    return read_json_content(json_file_name)
