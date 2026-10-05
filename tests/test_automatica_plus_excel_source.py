from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pytest

from tests.fixture_source import fixture_files

from gps_analyst.sources.automatica_plus_excel import (
    AutomaticaPlusExcelSource,
)






@pytest.fixture(scope="module")
def parsed_files():
    files = fixture_files()

    assert files, (
        "No hay fixtures XLSX disponibles. "
        "Revisa la configuración de la fuente de fixtures."
    )

    source = AutomaticaPlusExcelSource()

    return [
        source.load(path)
        for path in files
    ]


def test_all_fixture_workbooks_parse(parsed_files):
    assert parsed_files

    for data in parsed_files:
        assert data.days


def test_all_fixture_workbooks_validate(parsed_files):
    failures = []

    for data in parsed_files:
        if data.validation_issues:
            failures.append(
                (
                    data.source_path.name,
                    data.validation_issues,
                )
            )

    assert not failures, failures


def test_opening_rows_are_not_counted_as_real_trips(parsed_files):
    openings = [
        event
        for data in parsed_files
        for day in data.days
        for event in day.events
        if event.kind == "opening"
    ]

    assert openings

    for event in openings:
        assert event.stop_at is None
        assert event.restart_at is not None
        assert event.driving_seconds is None
        assert event.stop_seconds is None
        assert event.distance_km == 0.0
        assert event.max_speed_kmh == 0.0


def test_real_export_contains_carried_values_on_some_opening_rows(parsed_files):
    carried = [
        event
        for data in parsed_files
        for day in data.days
        for event in day.events
        if event.kind == "opening"
        and (
            (event.raw_distance_km or 0.0) > 0.0
            or (event.raw_max_speed_kmh or 0.0) > 0.0
        )
    ]

    assert carried, (
        "Los fixtures actuales no contienen el caso real observado "
        "de km/velocidad arrastrados a una fila de apertura."
    )

    for event in carried:
        assert event.distance_km == 0.0
        assert event.max_speed_kmh == 0.0


def test_closing_rows_preserve_last_real_trip(parsed_files):
    closings = [
        event
        for data in parsed_files
        for day in data.days
        for event in day.events
        if event.kind == "closing"
    ]

    assert closings

    for event in closings:
        assert event.stop_at is not None
        assert event.restart_at is None
        assert event.driving_seconds is not None
        assert event.stop_seconds is None
        assert event.distance_km is not None


def test_days_without_activity_are_supported(parsed_files):
    inactive_days = [
        day
        for data in parsed_files
        for day in data.days
        if not day.has_activity
    ]

    assert inactive_days

    for day in inactive_days:
        assert day.jornada_seconds == 0
        assert day.driving_seconds == 0
        assert day.stop_seconds == 0
        assert day.distance_km == 0.0
        assert not day.events


def test_duplicate_vehicle_days_are_consistent_between_exports(parsed_files):
    signatures = defaultdict(set)

    for data in parsed_files:
        for day in data.days:
            key = (
                day.vehicle,
                day.block_date,
            )

            signature = (
                day.start_at,
                day.end_at,
                day.jornada_seconds,
                day.driving_seconds,
                day.stop_seconds,
                day.max_speed_kmh,
                day.distance_km,
            )

            signatures[key].add(signature)

    duplicates = {
        key: values
        for key, values in signatures.items()
        if sum(
            1
            for data in parsed_files
            for day in data.days
            if (day.vehicle, day.block_date) == key
        )
        > 1
    }

    assert duplicates, (
        "Los fixtures deberían contener al menos un mismo vehículo/día "
        "exportado en más de un archivo."
    )

    inconsistent = {
        key: values
        for key, values in duplicates.items()
        if len(values) != 1
    }

    assert not inconsistent, inconsistent


def test_summary_math_is_coherent(parsed_files):
    for data in parsed_files:
        for day in data.days:
            assert (
                day.jornada_seconds
                == day.driving_seconds + day.stop_seconds
            )

            if not day.has_activity:
                continue

            assert (
                day.computed_driving_seconds
                == day.driving_seconds
            )

            assert (
                day.computed_stop_seconds
                == day.stop_seconds
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

            assert abs(
                day.computed_distance_km - day.distance_km
            ) <= distance_tolerance


def test_missing_opening_contamination_is_normalized(parsed_files):
    normalized = [
        (day, day.events[0])
        for data in parsed_files
        for day in data.days
        if (
            day.has_activity
            and day.events
            and day.events[0].kind != "opening"
            and day.events[0].raw_distance_km is not None
            and day.events[0].distance_km
            != day.events[0].raw_distance_km
        )
    ]

    assert normalized, (
        "Los fixtures privados deberian cubrir al menos un caso "
        "de apertura omitida con datos arrastrados."
    )

    for day, first in normalized:
        assert first.raw_distance_km is not None
        assert first.distance_km is not None

        assert first.raw_distance_km > first.distance_km
        assert first.max_speed_kmh is None

        real_event_count = sum(
            1
            for event in day.events
            if event.kind != "opening"
        )

        distance_tolerance = (
            (real_event_count + 1) * 0.05
            + 0.001
        )

        assert abs(
            day.computed_distance_km - day.distance_km
        ) <= distance_tolerance


def test_real_exports_allow_decimal_rounding_accumulation(parsed_files):
    rounding_cases = []

    for data in parsed_files:
        for day in data.days:
            if not day.has_activity:
                continue

            difference = abs(
                day.computed_distance_km - day.distance_km
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

            if 0.11 < difference <= distance_tolerance:
                rounding_cases.append(difference)

    assert len(rounding_cases) >= 2, (
        "Los fixtures privados deberian cubrir varios casos reales "
        "de acumulacion de redondeo decimal."
    )
