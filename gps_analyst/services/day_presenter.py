from __future__ import annotations

from gps_analyst.models.analysis import GpsDayAnalysis
from gps_analyst.models.presentation import (
    GpsDayView,
    GpsTimelineItemView,
)


class GpsDayPresenter:
    def present(
        self,
        analysis: GpsDayAnalysis,
    ) -> GpsDayView:
        timeline: list[GpsTimelineItemView] = []

        for index, trip in enumerate(analysis.trips):
            timeline.append(
                GpsTimelineItemView(
                    kind="trip",
                    index=trip.index,
                    start_at=trip.start_at,
                    end_at=trip.end_at,
                    start_text=self._format_clock(trip.start_at),
                    end_text=self._format_clock(trip.end_at),
                    duration_text=self._format_duration(
                        trip.duration_seconds
                    ),
                    label=f"Trayecto {trip.index}",
                    location_text=(
                        trip.destination_address
                        or "Destino no disponible"
                    ),
                    distance_text=self._format_distance(
                        trip.distance_km
                    ),
                    speed_text=self._format_speed(
                        trip.max_speed_kmh
                    ),
                    map_target=trip.map_target,
                )
            )

            if index < len(analysis.stops):
                stop = analysis.stops[index]

                timeline.append(
                    GpsTimelineItemView(
                        kind="stop",
                        index=stop.index,
                        start_at=stop.start_at,
                        end_at=stop.end_at,
                        start_text=self._format_clock(
                            stop.start_at
                        ),
                        end_text=self._format_clock(
                            stop.end_at
                        ),
                        duration_text=self._format_duration(
                            stop.duration_seconds
                        ),
                        label=self._stop_label(
                            stop.index,
                            stop.stop_type,
                        ),
                        location_text=(
                            stop.address
                            or "Ubicación no disponible"
                        ),
                        distance_text=None,
                        speed_text=None,
                        map_target=stop.map_target,
                    )
                )

        return GpsDayView(
            vehicle=analysis.vehicle,
            block_date=analysis.block_date,
            date_text=analysis.block_date.strftime(
                "%d/%m/%Y"
            ),
            active=analysis.start_at is not None,
            start_text=(
                self._format_clock(analysis.start_at)
                if analysis.start_at is not None
                else "—"
            ),
            end_text=(
                self._format_clock(analysis.end_at)
                if analysis.end_at is not None
                else "—"
            ),
            jornada_text=self._format_duration(
                analysis.jornada_seconds
            ),
            driving_text=self._format_duration(
                analysis.driving_seconds
            ),
            stop_text=self._format_duration(
                analysis.stop_seconds
            ),
            distance_text=self._format_distance(
                analysis.distance_km
            ),
            max_speed_text=self._format_speed(
                analysis.max_speed_kmh
            ),
            timeline=tuple(timeline),
            validation_issues=analysis.validation_issues,
        )

    def render_text(
        self,
        view: GpsDayView,
    ) -> str:
        lines = [
            f"Vehículo: {view.vehicle}",
            f"Fecha: {view.date_text}",
        ]

        if not view.active:
            lines.extend(
                [
                    "Estado: Sin actividad",
                    f"Kilómetros: {view.distance_text}",
                ]
            )
            return "\n".join(lines)

        lines.extend(
            [
                f"Inicio: {view.start_text}",
                f"Fin: {view.end_text}",
                f"Jornada: {view.jornada_text}",
                f"Conducción: {view.driving_text}",
                f"Paradas: {view.stop_text}",
                f"Kilómetros: {view.distance_text}",
                f"Velocidad punta: {view.max_speed_text}",
                "",
                "Cronología:",
            ]
        )

        for item in view.timeline:
            if item.kind == "trip":
                lines.append(
                    f"  {item.start_text} - {item.end_text} | "
                    f"{item.label} | "
                    f"{item.duration_text} | "
                    f"{item.distance_text} | "
                    f"{item.speed_text} | "
                    f"{item.location_text}"
                )
            else:
                lines.append(
                    f"  {item.start_text} - {item.end_text} | "
                    f"{item.label} | "
                    f"{item.duration_text} | "
                    f"{item.location_text}"
                )

        return "\n".join(lines)

    @staticmethod
    def _format_clock(value) -> str:
        return value.strftime("%H:%M:%S")

    @staticmethod
    def _format_duration(seconds: int) -> str:
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)

        parts: list[str] = []

        if hours:
            parts.append(f"{hours} h")

        if minutes:
            parts.append(f"{minutes} min")

        if secs or not parts:
            parts.append(f"{secs} s")

        return " ".join(parts)

    @staticmethod
    def _format_distance(value: float) -> str:
        return f"{value:.1f} km"

    @staticmethod
    def _format_speed(
        value: float | None,
    ) -> str:
        if value is None:
            return "—"

        if float(value).is_integer():
            return f"{int(value)} km/h"

        return f"{value:.1f} km/h"

    @staticmethod
    def _stop_label(
        index: int,
        stop_type: str | None,
    ) -> str:
        if stop_type == "P":
            description = "motor parado"
        elif stop_type == "E":
            description = "espera a ralentí"
        else:
            description = "tipo no indicado"

        return f"Parada {index} · {description}"