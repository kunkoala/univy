from fastapi import APIRouter
from fastapi import Depends

from univy.auth.security import get_current_user
from univy.smart_notes.utils import retrieve_material

router = APIRouter(prefix="/smart-notes", tags=["smart-notes"])


@router.get("/retrieve-material")
async def retrieve_material(doc_id: str, current_user=Depends(get_current_user)):
    return await retrieve_material(doc_id)
