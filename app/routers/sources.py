from typing import Literal, Optional
from fastapi import APIRouter, HTTPException
from app.techniques.webscrapper import WebScraper
from app.services.embeddings import EmbeddingService
from app.controllers.web_sources import WebSourcesController
from app.dependencies import get_sources_repo, get_vector_repo, get_config

router = APIRouter()

DEFAULT_WORKSPACE_ID = "c85f9a6e-1c0a-417f-b472-af714b6fab90"
DEFAULT_TECHNIQUE_ID = "ef0da8d0-eb02-485a-9700-532c36a64790"

@router.get("/scrape/urls", operation_id="scrape_urls")
async def scrape_urls(url: str):
    try:
        webscraper = WebScraper(scrapper_path="./bin/scrapper")
        links = webscraper.list_links(url)
        return {
            "status": "success",
            "message": "Links retrieved successfully",
            "data": links,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/{workspace_id}/add", operation_id="add_source")
async def add_source(technique_type: Literal["website"], urls: list[str], workspace_id: str, bot_id: Optional[str] = None):
    try:
        technique = get_sources_repo().get_technique(technique_type)
        if technique and technique_type == "website":
            web_source_controller = WebSourcesController(
                workspace_id=workspace_id,
                technique_id=technique.id,
                config=get_config(),
                source_repo=get_sources_repo(),
                vector_repo=get_vector_repo()
            )
            web_source_controller.start_scrapping(urls, bot_id)
            return {"status": "success", "message": "Sources and embeddings added successfully"}
        else:
            raise HTTPException(status_code=404, detail="Technique not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/{workspace_id}/semantic", operation_id="semantic_search")
async def semantic_search(workspace_id: str, prompt: str, top_k: int = 5):
    try:
        source_ids = get_sources_repo().get_source_ids_of_workspace(workspace_id)
        embedding_service = EmbeddingService()
        results = embedding_service.search_embeddings(
            query_text=prompt,
            source_ids=source_ids,
            top_k=top_k
        )
        return {
            "status": "success",
            "message": "Data retrieved successfully",
            "data": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))