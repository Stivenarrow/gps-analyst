from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path
from types import SimpleNamespace

import pytest

from gps_analyst.app import (
    _preferred_date_text,
    _qualities_by_vehicle_for_date,
)
from gps_analyst.models.gps import (
    GpsDetailEvent,
    GpsWorkbookData,
    VehicleDay,
)
from gps_analyst.services.workbook_session import GpsWorkbookSession
from gps_analyst.sources.automatica_plus_excel import (
    AutomaticaPlusExcelSource,
)


DAY = date(2026, 1, 15)
VEHICLE = "VEHICLE SYNTHETIC"


def _event(
    *,
    kind: str,
    stop_at: time | None,
    restart_at: time | None,
    driving_seconds: int | None,
    stop_seconds: int | None,
    distance_km: float,
    max_speed_kmh: float = 90.0,
) -> GpsDetailEvent:
    return GpsDetailEvent(
        vehicle=VEHICLE,
        block_date=DAY,
        kind=kind,
        stop_at=stop_at,
        restart_at=restart_at,
        driving_seconds=driving_seconds,
        stop_seconds=stop_seconds,
        max_speed_kmh=max_speed_kmh,
        distance_km=distance_km,
        raw_max_speed_kmh=max_speed_kmh,
        raw_distance_km=distance_km,
        stop_type=None,
        address=None,
        map_target=None,
    )


def _summary(
    *,
    start: datetime,
    end: datetime,
    driving: int,
    stop: int,
    distance: float,
    max_speed: float = 100.0,
) -> dict[str, object]:
    return {
        "vehicle": VEHICLE,
        "block_date": DAY,
        "start_at": start,
        "end_at": end,
        "jornada_seconds": driving + stop,
        "driving_seconds": driving,
        "stop_seconds": stop,
        "max_speed_kmh": max_speed,
        "distance_km": distance,
    }


def test_missing_opening_distance_is_reconciled_from_summary():
    source = AutomaticaPlusExcelSource()
    summary = _summary(
        start=datetime(2026, 1, 15, 6, 34, 12),
        end=datetime(2026, 1, 15, 7, 43, 1),
        driving=3930,
        stop=199,
        distance=70.8,
    )
    events = (
        _event(
            kind="segment",
            stop_at=time(6, 58, 20),
            restart_at=time(7, 1, 39),
            driving_seconds=1448,
            stop_seconds=199,
            distance_km=20.0,
            max_speed_kmh=83.0,
        ),
        _event(
            kind="closing",
            stop_at=time(7, 43, 1),
            restart_at=None,
            driving_seconds=2482,
            stop_seconds=None,
            distance_km=58.0,
            max_speed_kmh=91.0,
        ),
    )

    normalized = source._normalize_events_for_summary(summary, events)

    assert normalized[0].distance_km == 12.8
    assert normalized[0].driving_seconds == 1448
    assert sum(event.distance_km or 0.0 for event in normalized) == 70.8


def test_zero_duration_start_segment_becomes_opening_marker():
    source = AutomaticaPlusExcelSource()
    summary = _summary(
        start=datetime(2026, 1, 15, 3, 14, 46),
        end=datetime(2026, 1, 15, 3, 24, 46),
        driving=600,
        stop=0,
        distance=10.0,
    )
    events = (
        _event(
            kind="segment",
            stop_at=time(3, 14, 46),
            restart_at=time(3, 14, 46),
            driving_seconds=0,
            stop_seconds=0,
            distance_km=6.9,
            max_speed_kmh=76.0,
        ),
        _event(
            kind="closing",
            stop_at=time(3, 24, 46),
            restart_at=None,
            driving_seconds=600,
            stop_seconds=None,
            distance_km=10.0,
        ),
    )

    normalized = source._normalize_events_for_summary(summary, events)

    assert normalized[0].kind == "opening"
    assert normalized[0].distance_km == 0.0
    assert normalized[0].driving_seconds is None
    assert normalized[1].distance_km == 10.0


def test_carried_driving_duration_is_rebuilt_from_timeline():
    source = AutomaticaPlusExcelSource()
    summary = _summary(
        start=datetime(2026, 1, 15, 6, 0, 0),
        end=datetime(2026, 1, 15, 6, 30, 0),
        driving=1200,
        stop=600,
        distance=20.0,
    )
    events = (
        _event(
            kind="segment",
            stop_at=time(6, 10, 0),
            restart_at=time(6, 10, 0),
            driving_seconds=600,
            stop_seconds=0,
            distance_km=8.0,
        ),
        _event(
            kind="segment",
            stop_at=time(6, 10, 0),
            restart_at=time(6, 20, 0),
            driving_seconds=600,
            stop_seconds=600,
            distance_km=0.0,
        ),
        _event(
            kind="closing",
            stop_at=time(6, 30, 0),
            restart_at=None,
            driving_seconds=600,
            stop_seconds=None,
            distance_km=12.0,
        ),
    )

    normalized = source._normalize_events_for_summary(summary, events)

    assert normalized[1].driving_seconds == 0
    assert sum(
        event.driving_seconds or 0
        for event in normalized
        if event.kind != "opening"
    ) == 1200


def test_partial_activity_is_not_inactive():
    day = VehicleDay(
        vehicle=VEHICLE,
        block_date=DAY,
        start_at=None,
        end_at=datetime(2026, 1, 15, 14, 43, 59),
        jornada_seconds=1200,
        driving_seconds=600,
        stop_seconds=600,
        max_speed_kmh=80.0,
        distance_km=12.0,
        events=(),
    )

    assert day.has_activity
    assert day.has_partial_activity
    assert not day.has_complete_boundaries


class _PartialSource:
    def load(self, path: str | Path) -> GpsWorkbookData:
        partial = VehicleDay(
            vehicle=VEHICLE,
            block_date=DAY,
            start_at=None,
            end_at=datetime(2026, 1, 15, 14, 43, 59),
            jornada_seconds=1200,
            driving_seconds=600,
            stop_seconds=600,
            max_speed_kmh=80.0,
            distance_km=12.0,
            events=(),
        )
        return GpsWorkbookData(
            source_path=Path(path),
            export_start=None,
            export_end=None,
            totals=(),
            days=(partial,),
            validation_issues=(),
        )


def test_session_keeps_partial_day_inspectable(tmp_path):
    session = GpsWorkbookSession()
    session._source = _PartialSource()

    session.load(tmp_path / "synthetic.xlsx")

    assert session.day_count == 1
    assert session.vehicles == (VEHICLE,)
    view = session.view_for(VEHICLE, DAY)
    assert view.quality == "partial"
    assert view.active
    assert view.timeline == ()
    assert any(
        "falta inicio" in detail
        for detail in view.quality_details
    )
    assert len(session.warnings) == 1
    assert "jornada parcial" in session.warnings[0]

class _RecoverableDayIssueSource:
    def load(self, path: str | Path) -> GpsWorkbookData:
        bad_vehicle = "VEHICLE BAD"
        good_vehicle = "VEHICLE GOOD"

        bad = VehicleDay(
            vehicle=bad_vehicle,
            block_date=DAY,
            start_at=datetime(2026, 1, 15, 6, 0, 0),
            end_at=datetime(2026, 1, 15, 6, 10, 0),
            jornada_seconds=600,
            driving_seconds=600,
            stop_seconds=0,
            max_speed_kmh=80.0,
            distance_km=10.0,
            events=(),
        )
        good = VehicleDay(
            vehicle=good_vehicle,
            block_date=DAY,
            start_at=datetime(2026, 1, 15, 7, 0, 0),
            end_at=datetime(2026, 1, 15, 7, 10, 0),
            jornada_seconds=600,
            driving_seconds=600,
            stop_seconds=0,
            max_speed_kmh=80.0,
            distance_km=10.0,
            events=(
                GpsDetailEvent(
                    vehicle=good_vehicle,
                    block_date=DAY,
                    kind="closing",
                    stop_at=time(7, 10, 0),
                    restart_at=None,
                    driving_seconds=600,
                    stop_seconds=None,
                    max_speed_kmh=80.0,
                    distance_km=10.0,
                    raw_max_speed_kmh=80.0,
                    raw_distance_km=10.0,
                    stop_type=None,
                    address=None,
                    map_target=None,
                ),
            ),
        )

        return GpsWorkbookData(
            source_path=Path(path),
            export_start=None,
            export_end=None,
            totals=(),
            days=(bad, good),
            validation_issues=(
                f"{DAY.isoformat()} / {bad_vehicle}: "
                "conducción calculada 700s != resumen 600s",
            ),
        )


def test_session_keeps_incoherent_day_inspectable(tmp_path):
    session = GpsWorkbookSession()
    session._source = _RecoverableDayIssueSource()

    session.load(tmp_path / "synthetic.xlsx")

    assert session.day_count == 2
    assert session.vehicles == ("VEHICLE BAD", "VEHICLE GOOD")

    bad_view = session.view_for("VEHICLE BAD", DAY)
    good_view = session.view_for("VEHICLE GOOD", DAY)

    assert bad_view.quality == "incoherent"
    assert good_view.quality == "normal"
    assert bad_view.quality_details
    assert all(
        "!=" not in detail
        for detail in bad_view.quality_details
    )
    assert any(
        "Automatica PLUS" in detail
        or "cronolog" in detail.casefold()
        for detail in bad_view.quality_details
    )
    assert len(session.warnings) == 1
    assert "datos GPS incoherentes" in session.warnings[0]


class _StructuralIssueSource:
    def load(self, path: str | Path) -> GpsWorkbookData:
        return GpsWorkbookData(
            source_path=Path(path),
            export_start=None,
            export_end=None,
            totals=(),
            days=(),
            validation_issues=(
                "Totales: estructura global incoherente",
            ),
        )


def test_session_keeps_structural_validation_errors_blocking(tmp_path):
    session = GpsWorkbookSession()
    session._source = _StructuralIssueSource()

    with pytest.raises(ValueError, match="validación GPS"):
        session.load(tmp_path / "synthetic.xlsx")



def test_multiday_navigation_preserves_selected_date_when_available():
    first = date(2026, 1, 14)
    second = date(2026, 1, 15)
    date_map = {
        "14/01/2026": first,
        "15/01/2026": second,
    }

    assert (
        _preferred_date_text(
            "15/01/2026",
            date_map,
        )
        == "15/01/2026"
    )


def test_multiday_navigation_falls_back_when_date_is_unavailable():
    first = date(2026, 1, 14)
    date_map = {
        "14/01/2026": first,
    }

    assert (
        _preferred_date_text(
            "15/01/2026",
            date_map,
        )
        == "14/01/2026"
    )


def test_vehicle_quality_markers_are_scoped_to_selected_date():
    first = date(2026, 1, 14)
    second = date(2026, 1, 15)

    views = (
        SimpleNamespace(
            vehicle="VEHICLE ALPHA",
            block_date=first,
            quality="normal",
        ),
        SimpleNamespace(
            vehicle="VEHICLE ALPHA",
            block_date=second,
            quality="incoherent",
        ),
        SimpleNamespace(
            vehicle="VEHICLE BETA",
            block_date=second,
            quality="normal",
        ),
    )

    assert _qualities_by_vehicle_for_date(
        views,
        first,
    ) == {}

    assert _qualities_by_vehicle_for_date(
        views,
        second,
    ) == {
        "VEHICLE ALPHA": {"incoherent"},
    }

def test_presenter_translates_source_closing_issue_for_user():
    from gps_analyst.models.analysis import GpsDayAnalysis
    from gps_analyst.services.day_presenter import GpsDayPresenter

    issue = (
        f"{DAY.isoformat()} / {VEHICLE}: "
        "la última fila de detalle no es closing"
    )
    analysis = GpsDayAnalysis(
        vehicle=VEHICLE,
        block_date=DAY,
        start_at=datetime(2026, 1, 15, 6, 0, 0),
        end_at=datetime(2026, 1, 15, 6, 10, 0),
        jornada_seconds=600,
        driving_seconds=600,
        stop_seconds=0,
        distance_km=0.0,
        max_speed_kmh=80.0,
        trips=(),
        stops=(),
        validation_issues=(issue,),
        quality="incoherent",
        quality_details=(issue,),
    )

    view = GpsDayPresenter().present(analysis)

    assert any(
        "cierre de jornada" in detail
        for detail in view.quality_details
    )
    assert all(
        "closing" not in detail
        for detail in view.quality_details
    )
    assert all(
        VEHICLE not in detail
        for detail in view.quality_details
    )
    assert all(
        DAY.isoformat() not in detail
        for detail in view.quality_details
    )
