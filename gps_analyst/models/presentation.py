from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal


TimelineKind = Literal["trip", "stop"]


@dataclass(frozen=True)
class GpsTimelineItemView:
    kind: TimelineKind
    index: int

    start_at: datetime
    end_at: datetime

    start_text: str
    end_text: str
    duration_text: str

    label: str

    origin_text: str | None
    destination_text: str | None
    location_text: str

    distance_text: str | None
    speed_text: str | None

    map_target: str | None


@dataclass(frozen=True)
class GpsDayView:
    vehicle: str
    block_date: date

    date_text: str
    active: bool

    start_text: str
    end_text: str

    jornada_text: str
    driving_text: str
    stop_text: str

    distance_text: str
    max_speed_text: str

    timeline: tuple[GpsTimelineItemView, ...]

    validation_issues: tuple[str, ...]
    quality: str = "normal"
    quality_details: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.validation_issues