from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Literal


EventKind = Literal["opening", "segment", "closing"]


@dataclass(frozen=True)
class GpsDetailEvent:
    vehicle: str
    block_date: date
    kind: EventKind

    stop_at: time | None
    restart_at: time | None

    driving_seconds: int | None
    stop_seconds: int | None

    max_speed_kmh: float | None
    distance_km: float | None

    raw_max_speed_kmh: float | None
    raw_distance_km: float | None

    stop_type: str | None
    address: str | None
    map_target: str | None


@dataclass(frozen=True)
class VehicleTotal:
    vehicle: str
    jornada_seconds: int
    driving_seconds: int
    stop_seconds: int
    max_speed_kmh: float
    distance_km: float


@dataclass(frozen=True)
class VehicleDay:
    vehicle: str
    block_date: date

    start_at: datetime | None
    end_at: datetime | None

    jornada_seconds: int
    driving_seconds: int
    stop_seconds: int

    max_speed_kmh: float
    distance_km: float

    events: tuple[GpsDetailEvent, ...]

    @property
    def has_activity(self) -> bool:
        return (
            self.start_at is not None
            or self.end_at is not None
            or self.jornada_seconds != 0
            or self.driving_seconds != 0
            or self.stop_seconds != 0
            or abs(self.distance_km) > 0.001
            or bool(self.events)
        )

    @property
    def has_complete_boundaries(self) -> bool:
        return self.start_at is not None and self.end_at is not None

    @property
    def has_partial_activity(self) -> bool:
        return self.has_activity and not self.has_complete_boundaries

    @property
    def computed_driving_seconds(self) -> int:
        return sum(
            event.driving_seconds or 0
            for event in self.events
            if event.kind != "opening"
        )

    @property
    def computed_stop_seconds(self) -> int:
        return sum(
            event.stop_seconds or 0
            for event in self.events
            if event.kind == "segment"
        )

    @property
    def computed_distance_km(self) -> float:
        return round(
            sum(
                event.distance_km or 0.0
                for event in self.events
                if event.kind != "opening"
            ),
            3,
        )


@dataclass(frozen=True)
class GpsWorkbookData:
    source_path: Path
    export_start: datetime | None
    export_end: datetime | None

    totals: tuple[VehicleTotal, ...]
    days: tuple[VehicleDay, ...]

    validation_issues: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.validation_issues