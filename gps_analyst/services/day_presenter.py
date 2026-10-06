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
        previous_location: str | None = None

        for index, trip in enumerate(analysis.trips):
            trip_origin = (
                previous_location
                or "Origen no disponible"
            )

            trip_destination = (
                trip.destination_address
                or "Destino no disponible"
            )
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
                    origin_text=trip_origin,
                    destination_text=trip_destination,
                    location_text=trip_destination,
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
                        origin_text=None,
                        destination_text=None,
                        location_text=(
                            stop.address
                            or "Ubicación no disponible"
                        ),
                        distance_text=None,
                        speed_text=None,
                        map_target=stop.map_target,
                    )
                )

                previous_location = (
                    stop.address
                    or trip.destination_address
                    or previous_location
                )

        raw_quality_details = (
            analysis.quality_details
            or analysis.validation_issues
        )
        quality_details: list[str] = []

        if analysis.quality == "partial":
            quality_details.extend(raw_quality_details)

        elif analysis.quality == "incoherent":
            if (
                analysis.start_at is not None
                and analysis.end_at is not None
            ):
                elapsed_seconds = int(
                    (
                        analysis.end_at
                        - analysis.start_at
                    ).total_seconds()
                )
                summary_seconds = (
                    analysis.driving_seconds
                    + analysis.stop_seconds
                )
                summary_delta = (
                    summary_seconds
                    - elapsed_seconds
                )

                if summary_delta != 0:
                    quality_details.append(
                        (
                            "Entre inicio y fin transcurren "
                            f"{self._format_duration(elapsed_seconds)}, "
                            "pero el resumen de Automatica PLUS contabiliza "
                            f"{self._format_duration(summary_seconds)} "
                            "("
                            f"{self._format_duration(analysis.driving_seconds)} "
                            "de conducción + "
                            f"{self._format_duration(analysis.stop_seconds)} "
                            "parado). Hay una diferencia de "
                            f"{self._format_duration(abs(summary_delta))} "
                            + (
                                "por encima de la duración posible."
                                if summary_delta > 0
                                else "por debajo de la duración posible."
                            )
                        )
                    )

            for issue in raw_quality_details:
                source_prefix = (
                    f"{analysis.block_date.isoformat()} / "
                    f"{analysis.vehicle}: "
                )
                if issue.startswith(source_prefix):
                    issue = issue[len(source_prefix):]

                lowered = issue.casefold()

                if "la última fila de detalle no es closing" in lowered:
                    quality_details.append(
                        "La última fila de detalle no está marcada "
                        "como cierre de jornada."
                    )
                    continue

                if (
                    "trayecto temporal " in lowered
                    and " != detalle " in lowered
                ):
                    try:
                        event_text, values = issue.split(
                            ": trayecto temporal ",
                            1,
                        )
                        temporal_text, detail_text = values.split(
                            "s != detalle ",
                            1,
                        )
                        event_index = event_text.replace(
                            "Evento ",
                            "",
                        ).strip()
                        temporal_seconds = int(temporal_text)
                        detail_seconds = int(
                            detail_text.removesuffix("s")
                        )
                    except (ValueError, TypeError):
                        quality_details.append(issue)
                    else:
                        quality_details.append(
                            (
                                f"El evento {event_index} dura "
                                f"{self._format_duration(temporal_seconds)} "
                                "según sus horas registradas, pero "
                                "Automatica PLUS le atribuye "
                                f"{self._format_duration(detail_seconds)} "
                                "de conducción."
                            )
                        )
                    continue

                if (
                    "parada temporal " in lowered
                    and " != detalle " in lowered
                ):
                    try:
                        event_text, values = issue.split(
                            ": parada temporal ",
                            1,
                        )
                        temporal_text, detail_text = values.split(
                            "s != detalle ",
                            1,
                        )
                        event_index = event_text.replace(
                            "Evento ",
                            "",
                        ).strip()
                        temporal_seconds = int(temporal_text)
                        detail_seconds = int(
                            detail_text.removesuffix("s")
                        )
                    except (ValueError, TypeError):
                        quality_details.append(issue)
                    else:
                        quality_details.append(
                            (
                                f"La parada del evento {event_index} dura "
                                f"{self._format_duration(temporal_seconds)} "
                                "según sus horas registradas, pero "
                                "Automatica PLUS informa "
                                f"{self._format_duration(detail_seconds)}."
                            )
                        )
                    continue

                if (
                    "resumen" in lowered
                    and (
                        "conduccion reconstruida" in lowered
                        or "conducción reconstruida" in lowered
                        or "conduccion calculada" in lowered
                        or "conducción calculada" in lowered
                    )
                ):
                    continue

                if (
                    lowered.startswith("parada reconstruida ")
                    and " != resumen " in lowered
                ):
                    try:
                        rebuilt_text, summary_text = issue.split(
                            " != resumen ",
                            1,
                        )
                        rebuilt_seconds = int(
                            rebuilt_text.rsplit(" ", 1)[-1].removesuffix("s")
                        )
                        summary_seconds = int(
                            summary_text.removesuffix("s")
                        )
                    except (ValueError, TypeError):
                        pass
                    else:
                        quality_details.append(
                            (
                                "La cronología permite reconstruir "
                                f"{self._format_duration(rebuilt_seconds)} "
                                "de tiempo parado, frente a "
                                f"{self._format_duration(summary_seconds)} "
                                "indicados en el resumen."
                            )
                        )
                        continue

                if (
                    lowered.startswith("distancia reconstruida ")
                    and " != resumen " in lowered
                ):
                    try:
                        rebuilt_text, summary_text = issue.split(
                            " != resumen ",
                            1,
                        )
                        rebuilt_km = float(
                            rebuilt_text.rsplit(" ", 2)[-2]
                        )
                        summary_km = float(
                            summary_text.rsplit(" ", 1)[0]
                        )
                    except (ValueError, TypeError):
                        pass
                    else:
                        quality_details.append(
                            (
                                "La cronología suma "
                                f"{rebuilt_km:.1f} km, frente a "
                                f"{summary_km:.1f} km indicados "
                                "en el resumen."
                            )
                        )
                        continue

                if "!=" in issue:
                    quality_details.append(
                        "Se ha detectado una discrepancia interna "
                        "entre el detalle y el resumen de Automatica PLUS."
                    )
                    continue

                quality_details.append(issue)

            if (
                analysis.computed_driving_seconds
                != analysis.driving_seconds
            ):
                quality_details.append(
                    (
                        "La cronología permite reconstruir "
                        f"{self._format_duration(analysis.computed_driving_seconds)} "
                        "de conducción, frente a "
                        f"{self._format_duration(analysis.driving_seconds)} "
                        "indicados en el resumen."
                    )
                )

            if (
                analysis.computed_stop_seconds
                != analysis.stop_seconds
            ):
                quality_details.append(
                    (
                        "La cronología permite reconstruir "
                        f"{self._format_duration(analysis.computed_stop_seconds)} "
                        "de tiempo parado, frente a "
                        f"{self._format_duration(analysis.stop_seconds)} "
                        "indicados en el resumen."
                    )
                )

        else:
            quality_details.extend(raw_quality_details)

        quality_details = list(
            dict.fromkeys(quality_details)
        )

        return GpsDayView(
            vehicle=analysis.vehicle,
            block_date=analysis.block_date,
            date_text=analysis.block_date.strftime(
                "%d/%m/%Y"
            ),
            active=(
                analysis.start_at is not None
                or analysis.end_at is not None
                or analysis.jornada_seconds != 0
                or analysis.driving_seconds != 0
                or analysis.stop_seconds != 0
                or abs(analysis.distance_km) > 0.001
                or bool(analysis.trips)
                or bool(analysis.stops)
            ),
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
            quality=analysis.quality,
            quality_details=tuple(quality_details),
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
                    f"{item.origin_text} → "
                    f"{item.destination_text}"
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