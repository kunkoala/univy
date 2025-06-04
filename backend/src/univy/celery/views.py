from fastapi import APIRouter
from univy.celery.tasks import add, mul, xsum

router = APIRouter(prefix="/celery", tags=["celery"])

@router.get("/")
async def run_task_test():
    result = add.delay(4, 4)
    print(result)
    return f"Task result: {result}"

@router.get("/mul")
async def run_mul_task():
    result = mul.delay(4, 4)
    print(result)
    return f"Task result: {result}"


@router.get("/xsum")
async def run_xsum_task():
    result = xsum.delay([1, 2, 3, 4, 5])
    print(result)
    return f"Task result: {result}"