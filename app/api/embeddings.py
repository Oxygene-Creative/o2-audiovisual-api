from fastapi import APIRouter

router = APIRouter()

@router.get("/text")
def create_text_embeddings():
    return [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

@router.get("/image")
def create_iimage_embeddings(item_id: int):
    return {"id": item_id, "name": f"Item {item_id}"}