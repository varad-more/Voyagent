from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal, get_session
from app.models.itinerary import Itinerary
from app.schemas.itinerary import ItineraryRecord, ItineraryResponse, TripRequest
from app.services.itinerary_orchestrator import generate_itinerary
from app.utils.ics import build_ics


router = APIRouter(prefix="/api/itineraries", tags=["itineraries"])


async def _background_generate(itinerary_id: int, trip: TripRequest) -> None:
    async with SessionLocal() as session:
        result = await session.execute(select(Itinerary).where(Itinerary.id == itinerary_id))
        itinerary = result.scalar_one_or_none()
        if not itinerary:
            return
        try:
            response = await generate_itinerary(
                trip=trip, itinerary_id=itinerary_id, session=session
            )
            itinerary.status = "completed"
            itinerary.result_json = response.model_dump()
        except Exception as exc:  # pragma: no cover - external failures
            itinerary.status = "failed"
            itinerary.error_message = str(exc)
        await session.commit()


@router.post("", response_model=ItineraryRecord, status_code=status.HTTP_202_ACCEPTED)
async def queue_itinerary(
    trip: TripRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> ItineraryRecord:
    itinerary = Itinerary(status="queued", request_json=trip.model_dump())
    session.add(itinerary)
    await session.commit()
    await session.refresh(itinerary)

    background_tasks.add_task(_background_generate, itinerary.id, trip)
    return ItineraryRecord(
        id=itinerary.id,
        status=itinerary.status,
        request=trip,
        result=None,
        error_message=None,
        created_at=itinerary.created_at,
        updated_at=itinerary.updated_at,
    )


@router.post("/generate", response_model=ItineraryResponse)
async def generate_itinerary_route(
    trip: TripRequest,
    session: AsyncSession = Depends(get_session),
) -> ItineraryResponse:
    itinerary = Itinerary(status="processing", request_json=trip.model_dump())
    session.add(itinerary)
    await session.commit()
    await session.refresh(itinerary)

    try:
        result = await generate_itinerary(trip=trip, itinerary_id=itinerary.id, session=session)
    except Exception as exc:  # pragma: no cover - guardrail for external calls
        itinerary.status = "failed"
        itinerary.error_message = str(exc)
        await session.commit()
        raise HTTPException(status_code=500, detail="Failed to generate itinerary") from exc

    itinerary.status = "completed"
    itinerary.result_json = result.model_dump()
    await session.commit()
    return result


@router.get("/{itinerary_id}", response_model=ItineraryRecord)
async def get_itinerary(
    itinerary_id: int,
    session: AsyncSession = Depends(get_session),
) -> ItineraryRecord:
    result = await session.execute(select(Itinerary).where(Itinerary.id == itinerary_id))
    itinerary = result.scalar_one_or_none()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    response = ItineraryRecord(
        id=itinerary.id,
        status=itinerary.status,
        request=TripRequest.model_validate(itinerary.request_json),
        result=ItineraryResponse.model_validate(itinerary.result_json)
        if itinerary.result_json
        else None,
        error_message=itinerary.error_message,
        created_at=itinerary.created_at,
        updated_at=itinerary.updated_at,
    )
    return response


@router.get("/{itinerary_id}/ics")
async def download_ics(
    itinerary_id: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    result = await session.execute(select(Itinerary).where(Itinerary.id == itinerary_id))
    itinerary = result.scalar_one_or_none()
    if not itinerary or not itinerary.result_json:
        raise HTTPException(status_code=404, detail="Itinerary not ready")

    itinerary_response = ItineraryResponse.model_validate(itinerary.result_json)
    ics_content = build_ics(itinerary_response)
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=itinerary.ics"},
        status_code=status.HTTP_200_OK,
    )
