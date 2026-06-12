import pytest

from data.models.lap import Lap, CompoundType, TrackStatus
from data.models.race import Race, TrackInfo
from data.processors.gap_processor import GapProcessor
from data.processors.pit_window_processor import PitWindowProcessor
from data.statebuilder.state_builder import StateBuilder
from data.validators.race_validator import RaceValidator
from data.sources.fastf1_source import FastF1DataSource
from data.racerepository.race_repository import RaceRepository


def make_lap(
    driver: str,
    lap_number: int,
    lap_time_s: float = 90.0,
    position: int = 1,
    tyre_age: int = 10,
    total_laps: int = 20,
    track_status: TrackStatus = TrackStatus.GREEN,
) -> Lap:
    return Lap(
        driver=driver,
        lap_number=lap_number,
        lap_time_s=lap_time_s,
        compound_type=CompoundType.MEDIUM,
        tyre_age=tyre_age,
        position=position,
        gap_behind_s=999.0,
        gap_ahead_s=999.0,
        gap_to_leader_s=0.0,
        track_status=track_status,
        pitted=False,
        pit_time_s=None,
        lap_delta_s=0.0,
        pit_window=False,
        total_laps=total_laps,
    )


def make_small_race() -> Race:
    track = TrackInfo(
        name="TestTrack",
        total_laps=5,
        pit_loss_time_s=20.0,
        pit_window_start=2,
        pit_window_end=5,
    )

    laps_by_driver = {
        "D01": [
            make_lap("D01", 1, 90.0, position=1, tyre_age=10, total_laps=5),
            make_lap("D01", 2, 91.0, position=1, tyre_age=11, total_laps=5),
            make_lap("D01", 3, 92.0, position=1, tyre_age=12, total_laps=5),
        ],
        "D02": [
            make_lap("D02", 1, 92.0, position=2, tyre_age=10, total_laps=5),
            make_lap("D02", 2, 93.0, position=2, tyre_age=11, total_laps=5),
            make_lap("D02", 3, 94.0, position=2, tyre_age=12, total_laps=5),
        ],
        "D03": [
            make_lap("D03", 1, 95.0, position=3, tyre_age=10, total_laps=5),
            make_lap("D03", 2, 96.0, position=3, tyre_age=11, total_laps=5),
            make_lap("D03", 3, 97.0, position=3, tyre_age=12, total_laps=5),
        ],
    }

    return Race(track=track, year=2023, laps_by_driver=laps_by_driver)


def make_repository_race() -> Race:
    """
    Full fake race for RaceRepository integration tests.

    This matches your current validation config:
    - 15 drivers
    - 20 valid laps per driver
    """
    track = TrackInfo(
        name="TestTrack",
        total_laps=20,
        pit_loss_time_s=20.0,
        pit_window_start=8,
        pit_window_end=16,
    )

    laps_by_driver = {}

    for driver_index in range(1, 16):
        driver = f"D{driver_index:02d}"
        base_lap_time = 90.0 + driver_index

        laps = []
        for lap_number in range(1, 21):
            laps.append(
                make_lap(
                    driver=driver,
                    lap_number=lap_number,
                    lap_time_s=base_lap_time + lap_number * 0.1,
                    position=driver_index,
                    tyre_age=lap_number,
                    total_laps=20,
                )
            )

        laps_by_driver[driver] = laps

    return Race(track=track, year=2023, laps_by_driver=laps_by_driver)


class FakeRaceSource:
    """
    Fake replacement for FastF1DataSource.

    RaceRepository only needs an object with load_race().
    This avoids internet, FastF1 cache, and real race loading.
    """

    def __init__(self, race: Race):
        self.race = race

    def load_race(self, track_name: str, year: int) -> Race:
        return self.race


def test_lap_properties_work_correctly():
    lap = make_lap(
        driver="D01",
        lap_number=3,
        total_laps=10,
        track_status=TrackStatus.SAFETY_CAR,
    )

    assert lap.laps_remaining == 7
    assert lap.safety_car_flag is True
    assert lap.is_valid is True


def test_unknown_track_status_does_not_crash_safety_car_flag():
    lap = make_lap(
        driver="D01",
        lap_number=1,
        track_status=TrackStatus.UNKNOWN,
    )

    assert lap.safety_car_flag is False


def test_race_syncs_lap_total_laps_metadata():
    track = TrackInfo(
        name="TestTrack",
        total_laps=20,
        pit_loss_time_s=20.0,
    )

    lap = make_lap(
        driver="D01",
        lap_number=1,
        total_laps=999,
    )

    race = Race(
        track=track,
        year=2023,
        laps_by_driver={"D01": [lap]},
    )

    assert race.total_laps == 20
    assert race.get_driver_laps("D01")[0].total_laps == 20


def test_parse_track_status_known_values():
    assert FastF1DataSource._parse_track_status("1") == TrackStatus.GREEN
    assert FastF1DataSource._parse_track_status("2") == TrackStatus.YELLOW
    assert FastF1DataSource._parse_track_status("4") == TrackStatus.SAFETY_CAR
    assert FastF1DataSource._parse_track_status("5") == TrackStatus.RED_FLAG
    assert FastF1DataSource._parse_track_status("6") == TrackStatus.VIRTUAL_SC


def test_parse_track_status_unknown_value_returns_unknown():
    """
    Protects against Bug 2.

    _parse_track_status() must never return None.
    """
    assert FastF1DataSource._parse_track_status("9") == TrackStatus.UNKNOWN
    assert FastF1DataSource._parse_track_status("") == TrackStatus.UNKNOWN


def test_gap_processor_updates_gap_fields_and_lap_delta():
    race = make_small_race()

    GapProcessor().process(race)

    d01_lap3 = race.get_driver_laps("D01")[2]
    d02_lap3 = race.get_driver_laps("D02")[2]

    assert d01_lap3.gap_to_leader_s == 0.0
    assert d02_lap3.gap_to_leader_s > 0.0

    assert d01_lap3.gap_behind_s > 0.0
    assert d02_lap3.gap_ahead_s > 0.0

    assert d01_lap3.lap_delta_s >= 0.0
    assert d02_lap3.lap_delta_s >= 0.0


def test_pit_window_processor_sets_boolean_value():
    race = make_small_race()

    GapProcessor().process(race)
    PitWindowProcessor().process(race)

    for driver in race.drivers:
        for lap in race.get_driver_laps(driver):
            assert isinstance(lap.pit_window, bool)


def test_pit_window_true_during_safety_car_when_tyre_old_enough():
    track = TrackInfo(
        name="TestTrack",
        total_laps=5,
        pit_loss_time_s=20.0,
        pit_window_start=2,
        pit_window_end=5,
    )

    lap = make_lap(
        driver="D01",
        lap_number=2,
        tyre_age=15,
        total_laps=5,
        track_status=TrackStatus.SAFETY_CAR,
    )

    race = Race(
        track=track,
        year=2023,
        laps_by_driver={"D01": [lap]},
    )

    PitWindowProcessor().process(race)

    assert race.get_driver_laps("D01")[0].pit_window is True


def test_state_builder_creates_11_normalized_values():
    race = make_small_race()

    GapProcessor().process(race)
    PitWindowProcessor().process(race)

    builder = StateBuilder()
    states = builder.build_all(race, "D01")

    assert len(states) == len(race.get_valid_laps("D01"))

    for state in states:
        assert len(state) == 11

        for value in state:
            assert isinstance(value, float)
            assert 0.0 <= value <= 1.0


def test_race_validator_accepts_valid_state_vector():
    race = make_small_race()

    GapProcessor().process(race)
    PitWindowProcessor().process(race)

    lap = race.get_valid_laps("D01")[0]
    state = StateBuilder().build(lap, race.total_laps)

    validator = RaceValidator()

    assert validator.validate_state_vector(state, lap) is True


def test_race_validator_rejects_bad_state_vector_length():
    lap = make_lap("D01", 1)

    bad_state = [0.1, 0.2, 0.3]

    validator = RaceValidator()

    assert validator.validate_state_vector(bad_state, lap) is False


def test_race_validator_rejects_out_of_range_state_value():
    lap = make_lap("D01", 1)

    bad_state = [
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1.0,
        1.5,
    ]

    validator = RaceValidator()

    assert validator.validate_state_vector(bad_state, lap) is False


def test_race_repository_returns_full_list_of_state_vectors():
    """
    Protects against Bug 1.

    RaceRepository.get_states() must return List[List[float]],
    not only the final List[float].
    """
    race = make_repository_race()

    repo = RaceRepository(
        source=FakeRaceSource(race),
        validator=RaceValidator(),
        gap_proc=GapProcessor(),
        pit_proc=PitWindowProcessor(),
        builder=StateBuilder(),
    )

    states = repo.get_states(
        track_name="TestTrack",
        year=2023,
        driver="D01",
    )

    valid_laps = race.get_valid_laps("D01")

    assert isinstance(states, list)
    assert len(states) == len(valid_laps)

    for state in states:
        assert isinstance(state, list)
        assert len(state) == 11

        for value in state:
            assert isinstance(value, float)
            assert 0.0 <= value <= 1.0


def test_race_repository_get_laps_returns_valid_laps():
    race = make_repository_race()

    repo = RaceRepository(
        source=FakeRaceSource(race),
        validator=RaceValidator(),
        gap_proc=GapProcessor(),
        pit_proc=PitWindowProcessor(),
        builder=StateBuilder(),
    )

    laps = repo.get_laps(
        track_name="TestTrack",
        year=2023,
        driver="D01",
    )

    assert len(laps) == len(race.get_valid_laps("D01"))

    for lap in laps:
        assert lap.driver == "D01"
        assert lap.is_valid is True


def test_race_repository_rejects_unknown_driver():
    race = make_repository_race()

    repo = RaceRepository(
        source=FakeRaceSource(race),
        validator=RaceValidator(),
        gap_proc=GapProcessor(),
        pit_proc=PitWindowProcessor(),
        builder=StateBuilder(),
    )

    with pytest.raises(ValueError, match="Driver 'UNKNOWN' not in"):
        repo.get_states(
            track_name="TestTrack",
            year=2023,
            driver="UNKNOWN",
        )