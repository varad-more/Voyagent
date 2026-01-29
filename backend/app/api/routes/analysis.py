from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.core.gemini import GeminiClient
from app.utils.json_repair import best_effort_json
import structlog
import json

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = structlog.get_logger(__name__)

class ImageAnalysisResponse(BaseModel):
    destination: str | None
    interests: list[str]
    vibe: str
    season: str
    suggested_activities: list[str]

@router.post("/image", response_model=ImageAnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    content = await file.read()
    
    try:
        client = GeminiClient()
    except Exception as e:
        logger.error("gemini_init_failed", error=str(e))
        raise HTTPException(status_code=503, detail="AI Service Unavailable")

    prompt = """
    Analyze this travel-related image.
    Extract the likely destination (City, Country) if identifiable (or suggest a similar vibe/style destination if generic).
    Identify visible interests (e.g. Hiking, Food, Beach, History).
    Describe the vibe (e.g. Relaxing, Adventurous, Romantic).
    Suggest 3 activities based on the image.
    
    Return ONLY valid JSON matching this schema:
    {
      "destination": "City, Country",
      "interests": ["interest 1", "interest 2"],
      "vibe": "description",
      "season": "Best season guess",
      "suggested_activities": ["act 1", "act 2", "act 3"]
    }
    """
    
    try:
        raw_text = client.generate_from_image(content, prompt)
        data = best_effort_json(raw_text)
        return ImageAnalysisResponse(**data)
    except Exception as e:
        logger.error("image_analysis_failed", error=str(e))
        # Return a Stub if AI fails (or raise)
        raise HTTPException(status_code=500, detail=f"Failed to analyze image: {str(e)}")
