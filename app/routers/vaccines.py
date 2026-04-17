from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.dependencies import get_supabase_client, get_current_user
from app.schemas import BabyRead, VaccineRead, VaccineUpdate

router = APIRouter(prefix="/api", tags=["vaccines"])


@router.get("/baby", response_model=BabyRead)
async def get_baby(
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    """Get baby info."""
    result = supabase.table("baby").select("*").eq("id", 1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Baby record not found")
    return result.data[0]


@router.get("/vaccines", response_model=list[VaccineRead])
async def get_vaccines(
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    """Get all vaccines ordered by display_order."""
    result = (
        supabase.table("vaccines")
        .select("*")
        .order("display_order", desc=False)
        .execute()
    )
    return result.data


@router.get("/vaccines/{vaccine_id}", response_model=VaccineRead)
async def get_vaccine(
    vaccine_id: str,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    """Get a single vaccine by ID."""
    result = supabase.table("vaccines").select("*").eq("id", vaccine_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Vaccine not found")
    return result.data[0]


@router.patch("/vaccines/{vaccine_id}", response_model=VaccineRead)
async def update_vaccine(
    vaccine_id: str,
    body: VaccineUpdate,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Update a vaccine's done status and done_date.

    Validation:
    - If done=true, done_date is required (422 otherwise)
    - If done=false, done_date must be null (422 otherwise)
    """
    # Validation
    if body.done and body.done_date is None:
        raise HTTPException(
            status_code=422, detail="done_date is required when marking as done"
        )
    if not body.done and body.done_date is not None:
        raise HTTPException(
            status_code=422, detail="done_date must be null when marking as not done"
        )

    # Check vaccine exists
    existing = supabase.table("vaccines").select("id").eq("id", vaccine_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Vaccine not found")

    # Build update payload
    update_data = {
        "done": body.done,
        "done_date": body.done_date.isoformat() if body.done_date else None,
    }

    result = (
        supabase.table("vaccines")
        .update(update_data)
        .eq("id", vaccine_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update vaccine")

    return result.data[0]
