from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path

from gps_analyst.models.presentation import GpsDayView
from gps_analyst.services.day_presenter import GpsDayPresenter
from gps_analyst.services.journey_analysis import GpsDayAnalysisService
from gps_analyst.sources.automatica_plus_excel import (
    AutomaticaPlusExcelSource,
)


class GpsWorkbookSession:
    def __init__(self) -> None:
        self._source = AutomaticaPlusExcelSource()
        self._analyzer = GpsDayAnalysisService()
        self._presenter = GpsDayPresenter()

        self._source_path: Path | None = None
        self._warnings: tuple[str, ...] = ()
        self._views: dict[
            tuple[str, date],
            GpsDayView,
        ] = {}

    @property
    def source_path(self) -> Path | None:
        return self._source_path

    @property
    def day_count(self) -> int:
        return len(self._views)

    @property
    def warnings(self) -> tuple[str, ...]:
        return self._warnings

    @property
    def vehicles(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    vehicle
                    for vehicle, _ in self._views
                },
                key=str.casefold,
            )
        )

    @property
    def views(self) -> tuple[GpsDayView, ...]:
        return tuple(
            self._views[key]
            for key in sorted(
                self._views,
                key=lambda item: (
                    item[1],
                    item[0].casefold(),
                ),
            )
        )

    def load(
        self,
        path: str | Path,
    ) -> None:
        data = self._source.load(path)

        day_labels = {
            f"{day.block_date.isoformat()} / {day.vehicle}": (
                day.vehicle,
                day.block_date,
            )
            for day in data.days
        }
        recoverable_day_issues: dict[
            tuple[str, date],
            list[str],
        ] = {}
        blocking_issues: list[str] = []

        for issue in data.validation_issues:
            matched_key = next(
                (
                    key
                    for label, key in day_labels.items()
                    if issue.startswith(f"{label}:")
                ),
                None,
            )

            if matched_key is None:
                blocking_issues.append(issue)
                continue

            recoverable_day_issues.setdefault(
                matched_key,
                [],
            ).append(issue)

        if blocking_issues:
            detail = "\n".join(
                f"- {issue}"
                for issue in blocking_issues
            )

            raise ValueError(
                "El Excel no ha superado la validación GPS:\n"
                f"{detail}"
            )

        views: dict[
            tuple[str, date],
            GpsDayView,
        ] = {}
        warnings: list[str] = []

        for day in data.days:
            day_key = (day.vehicle, day.block_date)
            source_issues = tuple(
                recoverable_day_issues.get(day_key, ())
            )

            analysis = self._analyzer.analyze(day)

            combined_issues = tuple(
                dict.fromkeys(
                    (
                        *source_issues,
                        *analysis.validation_issues,
                    )
                )
            )

            if day.has_partial_activity:
                quality = "partial"
            elif combined_issues:
                quality = "incoherent"
            else:
                quality = analysis.quality

            if (
                combined_issues != analysis.validation_issues
                or quality != analysis.quality
            ):
                analysis = replace(
                    analysis,
                    validation_issues=combined_issues,
                    quality=quality,
                    quality_details=combined_issues,
                )

            view = self._presenter.present(analysis)

            if view.quality == "partial":
                warnings.append(
                    f"{day.block_date.isoformat()} / {day.vehicle}: "
                    "jornada parcial disponible para inspección."
                )
            elif view.quality == "incoherent":
                warnings.append(
                    f"{day.block_date.isoformat()} / {day.vehicle}: "
                    "jornada con datos GPS incoherentes disponible "
                    "para inspección."
                )

            key = (
                view.vehicle,
                view.block_date,
            )

            if key in views:
                raise ValueError(
                    "Jornada duplicada en el Excel: "
                    f"{view.block_date.isoformat()} / "
                    f"{view.vehicle}"
                )

            views[key] = view

        self._source_path = data.source_path
        self._warnings = tuple(warnings)
        self._views = views

    def dates_for_vehicle(
        self,
        vehicle: str,
    ) -> tuple[date, ...]:
        return tuple(
            sorted(
                block_date
                for current_vehicle, block_date
                in self._views
                if current_vehicle == vehicle
            )
        )

    def view_for(
        self,
        vehicle: str,
        block_date: date,
    ) -> GpsDayView:
        key = (
            vehicle,
            block_date,
        )

        try:
            return self._views[key]
        except KeyError as exc:
            raise KeyError(
                "No existe la jornada solicitada: "
                f"{block_date.isoformat()} / {vehicle}"
            ) from exc