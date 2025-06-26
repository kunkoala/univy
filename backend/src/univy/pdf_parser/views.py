from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

router = APIRouter(prefix="/pdf_parser", tags=["pdf_parser"])


pdf_parser_router = router
