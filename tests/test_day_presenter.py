from __future__ import annotations

from pathlib import Path

import pytest

from tests.fixture_source import fixture_files

from gps_analyst.services.day_presenter import (
    GpsDayPresenter,
)
from gps_analyst.services.journey_analysis import (
    GpsDayAnalysisService,
)
from gps_analyst.sources.automatica_plus_excel import (
    AutomaticaPlusExcelSource,
)




@pytest.fixture(scope="module")
def presented_days():
    source = AutomaticaPlusExcelSource()
    analyzer = GpsDayAnalysisService()
    presenter = GpsDayPresenter()

    result = []

    for path in fixture_files():
        data = source.load(path)

        assert data.is_valid

        for day in data.days:
            analysis = analyzer.analyze(day)

            assert analysis.is_valid

            view = presenter.present(analysis)

            result.append(
                (
                    day,
                    analysis,
                    view,
                )
            )

    assert result

    return result


def test_all_days_have_valid_views(presented_days):
    for _, analysis, view in presented_days:
        assert view.is_valid
        assert (
            view.validation_issues
            == analysis.validation_issues
        )


def test_active_day_summary_is_human_readable(presented_days):
    active = [
        view
        for day, _, view in presented_days
        if day.has_activity
    ]

    assert active

    for view in active:
        assert view.active
        assert view.start_text != "—"
        assert view.end_text != "—"

        assert "km" in view.distance_text
        assert "km/h" in view.max_speed_text

        assert view.jornada_text
        assert view.driving_text
        assert view.stop_text


def test_timeline_interleaves_trips_and_stops(presented_days):
    for day, analysis, view in presented_days:
        if not day.has_activity:
            continue

        assert len(view.timeline) == (
            len(analysis.trips)
            + len(analysis.stops)
        )

        assert view.timeline[0].kind == "trip"
        assert view.timeline[-1].kind == "trip"

        for index, item in enumerate(view.timeline):
            expected_kind = (
                "trip"
                if index % 2 == 0
                else "stop"
            )

            assert item.kind == expected_kind


def test_timeline_preserves_temporal_boundaries(presented_days):
    for day, analysis, view in presented_days:
        if not day.has_activity:
            continue

        assert view.timeline

        assert (
            view.timeline[0].start_at
            == analysis.start_at
        )

        assert (
            view.timeline[-1].end_at
            == analysis.end_at
        )

        for previous, current in zip(
            view.timeline,
            view.timeline[1:],
        ):
            assert previous.end_at == current.start_at


def test_timeline_preserves_locations_and_maps(presented_days):
    for day, analysis, view in presented_days:
        if not day.has_activity:
            continue

        trip_views = [
            item
            for item in view.timeline
            if item.kind == "trip"
        ]

        assert len(trip_views) == len(
            analysis.trips
        )

        for trip, item in zip(
            analysis.trips,
            trip_views,
        ):
            assert item.map_target == trip.map_target

            if trip.destination_address:
                assert (
                    item.destination_text
                    == trip.destination_address
                )
                assert (
                    item.location_text
                    == trip.destination_address
                )


def test_inactive_days_are_presented_as_empty(presented_days):
    inactive = [
        view
        for day, _, view in presented_days
        if not day.has_activity
    ]

    assert inactive

    for view in inactive:
        assert not view.active
        assert view.start_text == "—"
        assert view.end_text == "—"
        assert not view.timeline


def test_text_renderer_produces_complete_output(presented_days):
    presenter = GpsDayPresenter()

    active = next(
        view
        for day, _, view in presented_days
        if day.has_activity
    )

    text = presenter.render_text(active)

    assert active.vehicle in text
    assert active.date_text in text
    assert "Inicio:" in text
    assert "Fin:" in text
    assert "Jornada:" in text
    assert "Conducción:" in text
    assert "Paradas:" in text
    assert "Kilómetros:" in text
    assert "Cronología:" in text
    assert "Trayecto 1" in text

def test_trip_origins_follow_previous_stop(presented_days):
    checked_following_trip = False

    for day, analysis, view in presented_days:
        if not day.has_activity:
            continue

        trip_views = [
            item
            for item in view.timeline
            if item.kind == "trip"
        ]

        assert trip_views

        assert (
            trip_views[0].origin_text
            == "Origen no disponible"
        )

        for index in range(1, len(trip_views)):
            previous_stop = analysis.stops[index - 1]

            expected_origin = (
                previous_stop.address
                or analysis.trips[
                    index - 1
                ].destination_address
                or "Origen no disponible"
            )

            assert (
                trip_views[index].origin_text
                == expected_origin
            )

            checked_following_trip = True

    assert checked_following_trip
