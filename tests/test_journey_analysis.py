from __future__ import annotations

from pathlib import Path

import pytest

from gps_analyst.services.journey_analysis import (
    GpsDayAnalysisService,
)
from gps_analyst.sources.automatica_plus_excel import (
    AutomaticaPlusExcelSource,
)


FIXTURE_DIR = Path("data/private/fixtures")


@pytest.fixture(scope="module")
def analyzed_days():
    source = AutomaticaPlusExcelSource()
    service = GpsDayAnalysisService()

    files = sorted(FIXTURE_DIR.glob("*.xlsx"))

    assert files

    result = []

    for path in files:
        data = source.load(path)

        assert data.is_valid, (
            path.name,
            data.validation_issues,
        )

        for day in data.days:
            result.append(
                (
                    path,
                    day,
                    service.analyze(day),
                )
            )

    return result


def test_all_days_can_be_analyzed(analyzed_days):
    assert analyzed_days

    failures = [
        (
            path.name,
            day.block_date,
            analysis.validation_issues,
        )
        for path, day, analysis in analyzed_days
        if not analysis.is_valid
    ]

    assert not failures, failures


def test_active_days_reconstruct_complete_timeline(analyzed_days):
    active = [
        (day, analysis)
        for _, day, analysis in analyzed_days
        if day.has_activity
    ]

    assert active

    for day, analysis in active:
        assert analysis.trips

        assert analysis.trips[0].start_at == day.start_at
        assert analysis.trips[-1].end_at == day.end_at

        assert (
            analysis.computed_driving_seconds
            == day.driving_seconds
        )

        assert (
            analysis.computed_stop_seconds
            == day.stop_seconds
        )


def test_trip_and_stop_counts_follow_event_semantics(analyzed_days):
    for _, day, analysis in analyzed_days:
        if not day.has_activity:
            continue

        expected_trips = sum(
            1
            for event in day.events
            if event.kind != "opening"
        )

        expected_stops = sum(
            1
            for event in day.events
            if event.kind == "segment"
        )

        assert len(analysis.trips) == expected_trips
        assert len(analysis.stops) == expected_stops


def test_inactive_days_produce_empty_analysis(analyzed_days):
    inactive = [
        analysis
        for _, day, analysis in analyzed_days
        if not day.has_activity
    ]

    assert inactive

    for analysis in inactive:
        assert analysis.start_at is None
        assert analysis.end_at is None
        assert not analysis.trips
        assert not analysis.stops
        assert analysis.computed_driving_seconds == 0
        assert analysis.computed_stop_seconds == 0
        assert analysis.computed_distance_km == 0.0


def test_missing_opening_still_reconstructs_correctly(analyzed_days):
    cases = [
        (day, analysis)
        for _, day, analysis in analyzed_days
        if (
            day.has_activity
            and day.events
            and day.events[0].kind != "opening"
        )
    ]

    assert cases

    for day, analysis in cases:
        assert analysis.is_valid
        assert analysis.trips
        assert analysis.trips[0].start_at == day.start_at

        real_event_count = sum(
            1
            for event in day.events
            if event.kind != "opening"
        )

        tolerance = (
            (real_event_count + 1) * 0.05
            + 0.001
        )

        assert abs(
            analysis.computed_distance_km
            - day.distance_km
        ) <= tolerance

def test_timeline_is_contiguous(analyzed_days):
    for _, day, analysis in analyzed_days:
        if not day.has_activity:
            continue

        assert len(analysis.stops) == len(analysis.trips) - 1

        for index, stop in enumerate(analysis.stops):
            assert analysis.trips[index].end_at == stop.start_at
            assert stop.end_at == analysis.trips[index + 1].start_at

        for trip in analysis.trips:
            assert trip.duration_seconds >= 0

        for stop in analysis.stops:
            assert stop.duration_seconds >= 0
