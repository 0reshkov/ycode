from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_version():
    return {"version": "1.0.0"}

