from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.core.gemini import GeminiClient, generate_validated
from app.schemas.itinerary import ScheduleBlock
from app.utils.json_repair import best_effort_json
import structlog

router = APIRouter(prefix="/api/edit", tags=["edit"])
logger = structlog.get_logger(__name__)

class EditRequest(BaseModel):
    day_index: int
    block_index: int
    instruction: str
    current_block: dict
    destination: str

@router.post("/block", response_model=ScheduleBlock)
async def edit_block(request: EditRequest):
    try:
        client = GeminiClient()
    except Exception as e:
        raise HTTPException(status_code=503, detail="AI Service Unavailable")

    system_prompt = """
    You are an expert travel planner assisting with real-time itinerary modifications.
    The user wants to edit a specific schedule block.
    
    Rules:
    1. Maintain the same start/end times unless the user explicitly asks to change them.
    2. Ensure the new activity fits the location and constraints.
    3. Keep descriptions engaging but concise.
    4. If the user asks for a specific place, try to infer the address/details or use generic placeholders if unknown.
    """

    user_prompt = f"""
    Destination: {request.destination}
    
    Current Block:
    {request.current_block}
    
    User Instruction: "{request.instruction}"
    
    Please generate the updated ScheduleBlock based on this instruction.
    """
    
    try:
        # We can use generate_validated to get a strictly typed response
        new_block, _, _ = generate_validated(
            client=client,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_cls=ScheduleBlock
        )
        return new_block
    except Exception as e:
        logger.error("edit_block_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to edit block: {str(e)}")
