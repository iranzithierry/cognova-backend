from typing import Literal, Optional
from fastapi import APIRouter, HTTPException
from app.controllers.web_sources import WebSourcesController
from app.infrastructure.external.web.scraper import WebScraper
from app.api.dependencies import get_sources_repo, get_vector_repo, get_config

router = APIRouter()

@router.get("/scrape/urls", operation_id="scrape_urls")
async def scrape_urls(url: str):
    try:
        webscraper = WebScraper(scraper_path="../../../bin/scrapper")
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
        technique = await get_sources_repo().get_technique(technique_type)
        print(technique)
        if technique and technique_type == "website":
            web_source_controller = WebSourcesController(
                workspace_id=workspace_id,
                technique_id=technique.id,
            )
            await web_source_controller.start_scrapping(urls, bot_id)
            return {"status": "success", "message": "Sources and embeddings added successfully"}
        else:
            raise HTTPException(status_code=404, detail="Technique not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))