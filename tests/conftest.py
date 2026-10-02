from datetime import datetime, timedelta

import pytest
from flask import Flask
from sqlalchemy import event

from app import db
from models import Appointment, Doctor, Patient
from routes.appointments import appointments_bp
from routes.doctors import doctors_bp


@pytest.fixture()
def app():
    # Separate app on in-memory SQLite so tests never touch db/appointments.db
    test_app = Flask(__name__)
    test_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    test_app.config['TESTING'] = True
    db.init_app(test_app)
    test_app.register_blueprint(appointments_bp)
    test_app.register_blueprint(doctors_bp)
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def seed(app):
    """Two doctors, two patients; returns a helper to add appointments."""
    db.session.add_all([
        Doctor(id=1, name='Dr Alpha', department='GP'),
        Doctor(id=2, name='Dr Beta', department='Cardiology'),
        Patient(id=1, name='Pat One', dob='1980-01-01', nhs_number='111'),
        Patient(id=2, name='Pat Two', dob='1990-02-02', nhs_number='222'),
    ])
    db.session.commit()
    base = datetime(2025, 9, 1, 9, 0)

    def add(patient_id, doctor_id, slot):
        start = base + timedelta(hours=slot)
        appt = Appointment(patient_id=patient_id, doctor_id=doctor_id,
                           start_time=start, end_time=start + timedelta(minutes=30),
                           reason='test', status='scheduled')
        db.session.add(appt)
        db.session.commit()
        return appt

    return add


@pytest.fixture()
def count_queries(app):
    """Context manager counting SQL statements issued inside the block."""
    from contextlib import contextmanager

    @contextmanager
    def counter():
        statements = []

        def on_execute(*args):
            statements.append(args[2])

        event.listen(db.engine, 'before_cursor_execute', on_execute)
        try:
            yield statements
        finally:
            event.remove(db.engine, 'before_cursor_execute', on_execute)

    return counter
