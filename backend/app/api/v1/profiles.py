"""Profiles REST API endpoints.

Manages reusable organizational entities: Authorized Indian Agents, Foreign Manufacturers,
Domestic Manufacturers, and Manufacturing Sites.
"""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileResponse

router = APIRouter(prefix="/profiles", tags=["Organizational Profiles"])

# Maximum number of saved profiles to retain per entity category (rolling LRU buffer)
MAX_PROFILES_PER_TYPE = 6

DEFAULT_PROFILES = [
    {
        "profile_type": "INDIAN_AGENT",
        "name": "MedTech India Solutions Pvt Ltd",
        "data_payload": {
            "licence_number": "MD-42-DL-2024",
            "wholesale_licence": "DL-20B/21B-4491",
            "cin": "U33110DL2018PTC334912",
            "address": "Level 4, Statesman House, Barakhamba Road, Connaught Place, New Delhi 110001",
            "contact_email": "regulatory@medtechindia.example.com",
            "signatory_name": "Rajesh Kumar Sharma",
            "signatory_designation": "Director & Regulatory Head",
        },
    },
    {
        "profile_type": "FOREIGN_MANUFACTURER",
        "name": "SpineCraft Medical GmbH",
        "data_payload": {
            "country": "Germany",
            "iso_13485": "MDR-ISO-99412-DE",
            "iso_valid_until": "2028-11-30",
            "address": "Kronenstraße 44, 78532 Tuttlingen, Baden-Württemberg, Germany",
            "contact_person": "Dr. Klaus Weber",
            "designation": "Head of Quality & Regulatory Affairs",
        },
    },
    {
        "profile_type": "MANUFACTURING_SITE",
        "name": "Werk 2, Tuttlingen Cleanroom Facility",
        "data_payload": {
            "country": "Germany",
            "site_category": "PRIMARY_MANUFACTURING",
            "cleanroom_classification": "ISO Class 7 (Class 10,000)",
            "address": "Gewerbepark Nord 12, 78532 Tuttlingen, Germany",
            "operations": "Precision CNC Milling, Passivation & Cleanroom Packaging",
        },
    },
    {
        "profile_type": "DOMESTIC_MANUFACTURER",
        "name": "Apex BioMedical Devices India Ltd",
        "data_payload": {
            "licence_number": "MFG/MD/2023/00012",
            "cin": "U33111GJ2015PLC084120",
            "address": "Plot 42, GIDC BioTech Park, Savli, Vadodara, Gujarat 391775",
            "contact_email": "compliance@apexbio.example.com",
            "signatory_name": "Dr. Ananya Patel",
            "signatory_designation": "Managing Director",
        },
    },
    {
        "profile_type": "MANUFACTURING_SITE",
        "name": "Apex Plant 1, Vadodara Manufacturing Campus",
        "data_payload": {
            "country": "India",
            "site_category": "DOMESTIC_MANUFACTURING",
            "cleanroom_classification": "ISO Class 8 (Class 100,000)",
            "address": "Plot 42, GIDC BioTech Park, Savli, Vadodara, Gujarat 391775",
            "operations": "Device Assembly, Ultrasonic Cleaning, EO Sterilization & Testing",
        },
    },
]


@router.get(
    "",
    response_model=List[ProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="List organizational profiles",
)
async def list_profiles(
    profile_type: Optional[str] = Query(None, description="Filter by profile type"),
    db: AsyncSession = Depends(get_db),
) -> List[ProfileResponse]:
    """Retrieves organizational profiles. Auto-seeds statutory reference defaults if empty."""
    stmt = select(Profile)
    if profile_type:
        stmt = stmt.where(Profile.profile_type == profile_type)
    stmt = stmt.order_by(Profile.updated_at.desc(), Profile.name.asc())

    result = await db.execute(stmt)
    records = result.scalars().all()

    # Auto-seed if database has no profiles
    if not records and not profile_type:
        count_stmt = select(Profile)
        existing = (await db.execute(count_stmt)).scalars().first()
        if not existing:
            now = datetime.now(timezone.utc)
            for item in DEFAULT_PROFILES:
                p = Profile(
                    id=uuid.uuid4(),
                    profile_type=item["profile_type"],
                    name=item["name"],
                    data_payload=item["data_payload"],
                    created_at=now,
                    updated_at=now,
                )
                db.add(p)
            await db.commit()
            result = await db.execute(stmt)
            records = result.scalars().all()

    return list(records)


@router.post(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new organizational profile",
)
async def create_profile(
    payload: ProfileCreate,
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Creates or updates an organizational profile with deduplication and capacity pruning."""
    normalized_name = payload.name.strip()
    now = datetime.now(timezone.utc)

    # 1. Deduplication check: case-insensitive name match within same profile_type
    stmt = (
        select(Profile)
        .where(
            Profile.profile_type == payload.profile_type,
            func.lower(func.trim(Profile.name)) == func.lower(normalized_name),
        )
        .limit(1)
    )
    existing = (await db.execute(stmt)).scalars().first()

    if existing:
        # Update existing record (LRU touch & payload merge)
        merged_payload = {**(existing.data_payload or {}), **(payload.data_payload or {})}
        existing.data_payload = merged_payload
        existing.updated_at = now
        await db.commit()
        await db.refresh(existing)
        profile = existing
    else:
        profile = Profile(
            id=uuid.uuid4(),
            profile_type=payload.profile_type,
            name=normalized_name,
            data_payload=payload.data_payload or {},
            created_at=now,
            updated_at=now,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    # 2. Rolling Capacity Pruning: enforce MAX_PROFILES_PER_TYPE (LRU eviction)
    all_stmt = (
        select(Profile)
        .where(Profile.profile_type == payload.profile_type)
        .order_by(Profile.updated_at.desc(), Profile.created_at.desc())
    )
    all_profiles = (await db.execute(all_stmt)).scalars().all()

    if len(all_profiles) > MAX_PROFILES_PER_TYPE:
        stale_profiles = all_profiles[MAX_PROFILES_PER_TYPE:]
        for stale in stale_profiles:
            await db.delete(stale)
        await db.commit()

    return profile
