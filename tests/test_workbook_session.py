from __future__ import annotations

from pathlib import Path

import pytest

from tests.fixture_source import fixture_files

from gps_analyst.services.workbook_session import (
    GpsWorkbookSession,
)




@pytest.fixture(scope="module")
def loaded_sessions():
    files = fixture_files()

    assert files

    sessions = []

    for path in files:
        session = GpsWorkbookSession()
        session.load(path)

        sessions.append(
            (
                path,
                session,
            )
        )

    return sessions


def test_all_fixture_workbooks_load(loaded_sessions):
    for path, session in loaded_sessions:
        assert session.source_path == path
        assert session.day_count > 0
        assert session.views


def test_workbook_exposes_vehicle_selector(loaded_sessions):
    for _, session in loaded_sessions:
        assert session.vehicles

        assert session.vehicles == tuple(
            sorted(
                session.vehicles,
                key=str.casefold,
            )
        )


def test_vehicle_dates_are_ordered(loaded_sessions):
    for _, session in loaded_sessions:
        for vehicle in session.vehicles:
            dates = session.dates_for_vehicle(
                vehicle
            )

            assert dates
            assert dates == tuple(
                sorted(dates)
            )


def test_every_day_can_be_retrieved(loaded_sessions):
    for _, session in loaded_sessions:
        for view in session.views:
            selected = session.view_for(
                view.vehicle,
                view.block_date,
            )

            assert selected == view
            assert selected.is_valid


def test_inactive_days_remain_selectable(loaded_sessions):
    inactive = [
        view
        for _, session in loaded_sessions
        for view in session.views
        if not view.active
    ]

    assert inactive

    for view in inactive:
        assert not view.timeline
        assert view.start_text == "—"
        assert view.end_text == "—"


def test_application_module_imports_without_launching():
    from gps_analyst import app

    assert callable(app.main)