from __future__ import annotations

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

        if not data.is_valid:
            detail = "\n".join(
                f"- {issue}"
                for issue in data.validation_issues
            )

            raise ValueError(
                "El Excel no ha superado la validación GPS:\n"
                f"{detail}"
            )

        views: dict[
            tuple[str, date],
            GpsDayView,
        ] = {}

        for day in data.days:
            analysis = self._analyzer.analyze(day)

            if not analysis.is_valid:
                detail = "\n".join(
                    f"- {issue}"
                    for issue in analysis.validation_issues
                )

                raise ValueError(
                    "No se ha podido reconstruir una jornada:\n"
                    f"{detail}"
                )

            view = self._presenter.present(analysis)

            if not view.is_valid:
                raise ValueError(
                    "La jornada no ha superado "
                    "la validación de presentación."
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