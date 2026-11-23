from datetime import date

import pytest
from pydantic import ValidationError

from app.main import Tournament, tournament_status


def sample(**changes):
    data = dict(id="test", name="Test", sport="Гольф", start_date=date(2026, 5, 1),
                end_date=date(2026, 5, 2), country="Россия", location="Москва",
                level="Региональный", source_url="https://example.org/event")
    data.update(changes)
    return Tournament(**data)


def test_status_is_derived_from_dates():
    event = sample()
    assert tournament_status(event, date(2026, 4, 30)) == "scheduled"
    assert tournament_status(event, date(2026, 5, 1)) == "live"
    assert tournament_status(event, date(2026, 5, 3)) == "finished"


def test_end_date_before_start_date_is_rejected():
    with pytest.raises(ValidationError):
        sample(end_date=date(2026, 4, 30))
