from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class GpsTrip:
    index: int

    start_at: datetime
    end_at: datetime
    duration_seconds: int

    distance_km: float
    max_speed_kmh: float | None

    destination_type: str | None
    destination_address: str | None
    map_target: str | None


@dataclass(frozen=True)
class GpsStop:
    index: int

    start_at: datetime
    end_at: datetime
    duration_seconds: int

    stop_type: str | None
    address: str | None
    map_target: str | None


@dataclass(frozen=True)
class GpsDayAnalysis:
    vehicle: str
    block_date: date

    start_at: datetime | None
    end_at: datetime | None

    jornada_seconds: int
    driving_seconds: int
    stop_seconds: int

    distance_km: float
    max_speed_kmh: float

    trips: tuple[GpsTrip, ...]
    stops: tuple[GpsStop, ...]

    validation_issues: tuple[str, ...]
    quality: str = "normal"
    quality_details: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.validation_issues

    @property
    def computed_driving_seconds(self) -> int:
        return sum(
            trip.duration_seconds
            for trip in self.trips
        )

    @property
    def computed_stop_seconds(self) -> int:
        return sum(
            stop.duration_seconds
            for stop in self.stops
        )

    @property
    def computed_distance_km(self) -> float:
        return round(
            sum(
                trip.distance_km
                for trip in self.trips
            ),
            3,
        )