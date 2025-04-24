from fastapi import APIRouter
from app.analyzers.search_with_bodmas import SearchService
from pydantic import BaseModel

search_router = APIRouter()
search_service = SearchService()

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

@search_router.post("/search/{media_type}")
def search(media_type: str, search: SearchRequest ):
    results = search_service.search_index(
        index_name=f"{media_type}_*",
        query=search.query,
        size=search.limit
    )

    search_results = []

    for result in results:
        search_results.append(result["_source"])

    return search_results