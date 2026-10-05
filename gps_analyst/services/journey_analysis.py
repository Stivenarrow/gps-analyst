from __future__ import annotations

from datetime import datetime, time, timedelta

from gps_analyst.models.analysis import (
    GpsDayAnalysis,
    GpsStop,
    GpsTrip,
)
from gps_analyst.models.gps import VehicleDay


class GpsDayAnalysisService:
    def analyze(self, day: VehicleDay) -> GpsDayAnalysis:
        issues: list[str] = []

        if not day.has_activity:
            return GpsDayAnalysis(
                vehicle=day.vehicle,
                block_date=day.block_date,
                start_at=None,
                end_at=None,
                jornada_seconds=day.jornada_seconds,
                driving_seconds=day.driving_seconds,
                stop_seconds=day.stop_seconds,
                distance_km=day.distance_km,
                max_speed_kmh=day.max_speed_kmh,
                trips=(),
                stops=(),
                validation_issues=(),
            )

        if day.start_at is None or day.end_at is None:
            raise ValueError(
                "Una jornada activa debe contener inicio y fin."
            )

        trips: list[GpsTrip] = []
        stops: list[GpsStop] = []

        cursor = day.start_at

        for event in day.events:
            if event.kind == "opening":
                continue

            if event.stop_at is None:
                issues.append(
                    f"Evento {len(trips) + 1}: "
                    "trayecto sin hora PARA."
                )
                continue

            trip_end = self._clock_at_or_after(
                cursor,
                event.stop_at,
            )

            trip_seconds = int(
                (trip_end - cursor).total_seconds()
            )

            if trip_seconds < 0:
                issues.append(
                    f"Evento {len(trips) + 1}: "
                    "duracion de trayecto negativa."
                )
                continue

            if (
                event.driving_seconds is not None
                and trip_seconds != event.driving_seconds
            ):
                issues.append(
                    f"Evento {len(trips) + 1}: "
                    f"trayecto temporal {trip_seconds}s "
                    f"!= detalle {event.driving_seconds}s"
                )

            trips.append(
                GpsTrip(
                    index=len(trips) + 1,
                    start_at=cursor,
                    end_at=trip_end,
                    duration_seconds=trip_seconds,
                    distance_km=event.distance_km or 0.0,
                    max_speed_kmh=event.max_speed_kmh,
                    destination_type=event.stop_type,
                    destination_address=event.address,
                    map_target=event.map_target,
                )
            )

            if event.kind == "closing":
                cursor = trip_end
                continue

            if event.restart_at is None:
                issues.append(
                    f"Evento {len(trips)}: "
                    "segmento sin hora ARRANCA."
                )
                cursor = trip_end
                continue

            stop_end = self._clock_at_or_after(
                trip_end,
                event.restart_at,
            )

            stop_seconds = int(
                (stop_end - trip_end).total_seconds()
            )

            if stop_seconds < 0:
                issues.append(
                    f"Evento {len(trips)}: "
                    "duracion de parada negativa."
                )
                cursor = trip_end
                continue

            if (
                event.stop_seconds is not None
                and stop_seconds != event.stop_seconds
            ):
                issues.append(
                    f"Evento {len(trips)}: "
                    f"parada temporal {stop_seconds}s "
                    f"!= detalle {event.stop_seconds}s"
                )

            stops.append(
                GpsStop(
                    index=len(stops) + 1,
                    start_at=trip_end,
                    end_at=stop_end,
                    duration_seconds=stop_seconds,
                    stop_type=event.stop_type,
                    address=event.address,
                    map_target=event.map_target,
                )
            )

            cursor = stop_end

        if not trips:
            issues.append(
                "Jornada activa sin trayectos reconstruibles."
            )
        else:
            if trips[0].start_at != day.start_at:
                issues.append(
                    "El primer trayecto no empieza "
                    "en el inicio de jornada."
                )

            if trips[-1].end_at != day.end_at:
                issues.append(
                    "El ultimo trayecto no termina "
                    "en el final de jornada."
                )

        computed_driving = sum(
            trip.duration_seconds
            for trip in trips
        )

        computed_stop = sum(
            stop.duration_seconds
            for stop in stops
        )

        if computed_driving != day.driving_seconds:
            issues.append(
                f"Conduccion reconstruida {computed_driving}s "
                f"!= resumen {day.driving_seconds}s"
            )

        if computed_stop != day.stop_seconds:
            issues.append(
                f"Parada reconstruida {computed_stop}s "
                f"!= resumen {day.stop_seconds}s"
            )

        real_event_count = sum(
            1
            for event in day.events
            if event.kind != "opening"
        )

        distance_tolerance = (
            (real_event_count + 1) * 0.05
            + 0.001
        )

        computed_distance = round(
            sum(
                trip.distance_km
                for trip in trips
            ),
            3,
        )

        if (
            abs(computed_distance - day.distance_km)
            > distance_tolerance
        ):
            issues.append(
                f"Distancia reconstruida "
                f"{computed_distance:.3f} km "
                f"!= resumen {day.distance_km:.3f} km"
            )

        return GpsDayAnalysis(
            vehicle=day.vehicle,
            block_date=day.block_date,
            start_at=day.start_at,
            end_at=day.end_at,
            jornada_seconds=day.jornada_seconds,
            driving_seconds=day.driving_seconds,
            stop_seconds=day.stop_seconds,
            distance_km=day.distance_km,
            max_speed_kmh=day.max_speed_kmh,
            trips=tuple(trips),
            stops=tuple(stops),
            validation_issues=tuple(issues),
        )

    @staticmethod
    def _clock_at_or_after(
        reference: datetime,
        value: time,
    ) -> datetime:
        candidate = datetime.combine(
            reference.date(),
            value,
        )

        if candidate < reference:
            candidate += timedelta(days=1)

        return candidate