"""Agregados de consultations para el dashboard admin."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Optional

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Consultation
from app.schemas.admin import (
    AdminConsultationItem,
    AdminConsultationList,
    AdminStatsSummary,
    CountBucket,
)


def _as_utc_start(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def _as_utc_end(d: date) -> datetime:
    return datetime.combine(d, time.max, tzinfo=timezone.utc)


class AdminStatsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _base_filter(
        self,
        *,
        from_date: date | None,
        to_date: date | None,
    ):
        clauses = []
        if from_date is not None:
            clauses.append(Consultation.created_at >= _as_utc_start(from_date))
        if to_date is not None:
            clauses.append(Consultation.created_at <= _as_utc_end(to_date))
        return clauses

    async def summary(
        self,
        *,
        from_date: date | None = None,
        to_date: date | None = None,
        top_n: int = 15,
    ) -> AdminStatsSummary:
        filters = self._base_filter(from_date=from_date, to_date=to_date)

        total = int(
            await self.db.scalar(
                select(func.count()).select_from(Consultation).where(*filters)
            )
            or 0
        )

        by_activity = await self._group_counts(
            key_col=Consultation.activity_code,
            label_col=Consultation.activity_name,
            filters=filters,
            limit=top_n,
            empty_key="(sin rubro)",
        )
        by_commune = await self._group_counts(
            key_col=Consultation.commune,
            filters=filters,
            limit=top_n,
            empty_key="(sin comuna)",
        )
        by_neighborhood = await self._group_counts(
            key_col=Consultation.neighborhood,
            filters=filters,
            limit=top_n,
            empty_key="(sin barrio)",
        )
        by_status = await self._group_counts(
            key_col=Consultation.status,
            filters=filters,
            limit=50,
            empty_key="(sin status)",
        )
        by_zoning = await self._group_counts(
            key_col=Consultation.zoning_mixtura,
            filters=filters,
            limit=top_n,
            empty_key="(sin mixtura)",
        )

        # rubro_allowed as string buckets
        allowed_stmt = (
            select(
                Consultation.zoning_rubro_allowed,
                func.count().label("c"),
            )
            .where(*filters)
            .group_by(Consultation.zoning_rubro_allowed)
            .order_by(func.count().desc())
        )
        by_rubro_allowed: list[CountBucket] = []
        for allowed, count in (await self.db.execute(allowed_stmt)).all():
            if allowed is True:
                key, label = "true", "Permitido"
            elif allowed is False:
                key, label = "false", "No permitido"
            else:
                key, label = "null", "Sin dato"
            by_rubro_allowed.append(CountBucket(key=key, label=label, count=int(count)))

        day_stmt = (
            select(
                cast(Consultation.created_at, Date).label("day"),
                func.count().label("c"),
            )
            .where(*filters)
            .group_by(cast(Consultation.created_at, Date))
            .order_by(cast(Consultation.created_at, Date))
        )
        by_day = [
            CountBucket(key=str(day), label=str(day), count=int(count))
            for day, count in (await self.db.execute(day_stmt)).all()
            if day is not None
        ]

        return AdminStatsSummary(
            total=total,
            from_date=_as_utc_start(from_date) if from_date else None,
            to_date=_as_utc_end(to_date) if to_date else None,
            by_activity=by_activity,
            by_commune=by_commune,
            by_neighborhood=by_neighborhood,
            by_status=by_status,
            by_day=by_day,
            by_zoning_mixtura=by_zoning,
            by_rubro_allowed=by_rubro_allowed,
        )

    async def _group_counts(
        self,
        *,
        key_col,
        filters: list,
        limit: int,
        empty_key: str,
        label_col=None,
    ) -> list[CountBucket]:
        cols = [key_col, func.count().label("c")]
        if label_col is not None:
            cols.insert(1, func.max(label_col).label("label"))
        stmt = (
            select(*cols)
            .where(*filters)
            .group_by(key_col)
            .order_by(func.count().desc())
            .limit(limit)
        )
        rows = (await self.db.execute(stmt)).all()
        out: list[CountBucket] = []
        for row in rows:
            if label_col is not None:
                key, label, count = row[0], row[1], row[2]
            else:
                key, count = row[0], row[1]
                label = None
            key_s = str(key) if key not in (None, "") else empty_key
            out.append(
                CountBucket(
                    key=key_s,
                    label=str(label) if label else key_s,
                    count=int(count),
                )
            )
        return out

    async def list_consultations(
        self,
        *,
        from_date: date | None = None,
        to_date: date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AdminConsultationList:
        filters = self._base_filter(from_date=from_date, to_date=to_date)
        total = int(
            await self.db.scalar(
                select(func.count()).select_from(Consultation).where(*filters)
            )
            or 0
        )
        stmt = (
            select(Consultation)
            .where(*filters)
            .order_by(Consultation.created_at.desc())
            .limit(min(limit, 200))
            .offset(max(offset, 0))
        )
        rows = list(await self.db.scalars(stmt))
        items = [
            AdminConsultationItem(
                id=r.id,
                created_at=r.created_at,
                status=r.status,
                data_status_overall=r.data_status_overall,
                activity_code=r.activity_code,
                activity_name=r.activity_name,
                original_query=r.original_query,
                commune=r.commune,
                neighborhood=r.neighborhood,
                normalized_address=r.normalized_address,
                zoning_mixtura=r.zoning_mixtura,
                zoning_rubro_allowed=r.zoning_rubro_allowed,
                message=r.message,
            )
            for r in rows
        ]
        return AdminConsultationList(total=total, items=items)
