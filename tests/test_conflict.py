from datetime import datetime

from utils.conflict import check_overlap


def dt(hour, minute=0):
    return datetime(2025, 9, 1, hour, minute)


# seed(patient, doctor, slot) books slot N as 09:00+N hours for 30 minutes,
# so slot 0 is 09:00-09:30 for the given doctor.

def test_free_calendar_has_no_overlap(seed):
    assert check_overlap(1, dt(9), dt(9, 30)) is False


def test_exact_same_slot_overlaps(seed):
    seed(1, 1, 0)
    assert check_overlap(1, dt(9), dt(9, 30)) is True


def test_partial_overlap_at_start(seed):
    seed(1, 1, 0)
    assert check_overlap(1, dt(8, 45), dt(9, 15)) is True


def test_partial_overlap_at_end(seed):
    seed(1, 1, 0)
    assert check_overlap(1, dt(9, 15), dt(9, 45)) is True


def test_new_slot_inside_existing(seed):
    seed(1, 1, 0)
    assert check_overlap(1, dt(9, 10), dt(9, 20)) is True


def test_new_slot_contains_existing(seed):
    seed(1, 1, 0)
    assert check_overlap(1, dt(8), dt(10)) is True


def test_back_to_back_after_is_allowed(seed):
    seed(1, 1, 0)
    assert check_overlap(1, dt(9, 30), dt(10)) is False


def test_back_to_back_before_is_allowed(seed):
    seed(1, 1, 0)
    assert check_overlap(1, dt(8, 30), dt(9)) is False


def test_other_doctor_not_affected(seed):
    seed(1, 1, 0)
    assert check_overlap(2, dt(9), dt(9, 30)) is False


def test_cancelled_appointment_does_not_block(seed):
    from app import db
    appt = seed(1, 1, 0)
    appt.status = 'cancelled'
    db.session.commit()
    assert check_overlap(1, dt(9), dt(9, 30)) is False


def test_exclude_id_ignores_own_appointment(seed):
    appt = seed(1, 1, 0)
    assert check_overlap(1, dt(9), dt(9, 30), exclude_id=appt.id) is False


def test_exclude_id_still_detects_other_appointments(seed):
    appt = seed(1, 1, 0)
    seed(2, 1, 1)  # 10:00-10:30
    assert check_overlap(1, dt(10), dt(10, 30), exclude_id=appt.id) is True
