def test_list_doctors(client, seed):
    body = client.get('/doctors').get_json()
    assert body['status'] == 200 and body['error'] is None
    assert [d['name'] for d in body['data']] == ['Dr Alpha', 'Dr Beta']


def test_list_doctors_empty(client):
    assert client.get('/doctors').get_json()['data'] == []


def test_get_doctor(client, seed):
    resp = client.get('/doctors/1')
    assert resp.status_code == 200
    assert resp.get_json()['data'] == {'id': 1, 'name': 'Dr Alpha', 'department': 'GP'}


def test_get_doctor_not_found(client, seed):
    resp = client.get('/doctors/99')
    assert resp.status_code == 404
    assert resp.get_json() == {'data': None, 'error': 'Doctor not found', 'status': 404}


def test_delete_doctor_without_appointments(client, seed):
    resp = client.delete('/doctors/2')
    assert resp.status_code == 200
    assert resp.get_json()['data'] == {'id': 2, 'deleted': True}
    assert client.get('/doctors/2').status_code == 404


def test_delete_doctor_not_found(client, seed):
    assert client.delete('/doctors/99').status_code == 404


def test_delete_doctor_with_appointments_is_blocked(client, seed):
    seed(1, 1, 0)
    resp = client.delete('/doctors/1')
    assert resp.status_code == 409
    assert resp.get_json()['data'] is None
    assert client.get('/doctors/1').status_code == 200


def test_delete_doctor_blocked_even_by_cancelled_appointment(client, seed):
    appt = seed(1, 1, 0)
    client.delete(f'/appointments/{appt.id}')
    assert client.delete('/doctors/1').status_code == 409


def test_slots_only_returns_scheduled_for_that_doctor(client, seed):
    keep = seed(1, 1, 0)
    cancelled = seed(1, 1, 1)
    seed(1, 2, 2)
    client.delete(f'/appointments/{cancelled.id}')
    data = client.get('/doctors/1/slots').get_json()['data']
    assert data['doctor']['id'] == 1
    assert [s['id'] for s in data['booked_slots']] == [keep.id]


def test_slots_date_filter(client, seed):
    seed(1, 1, 0)    # 2025-09-01 09:00
    seed(1, 1, 24)   # 2025-09-02 09:00
    data = client.get('/doctors/1/slots?date=2025-09-02').get_json()['data']
    assert len(data['booked_slots']) == 1
    assert data['booked_slots'][0]['start_time'].startswith('2025-09-02')


def test_slots_date_filter_no_match(client, seed):
    seed(1, 1, 0)
    data = client.get('/doctors/1/slots?date=2030-01-01').get_json()['data']
    assert data['booked_slots'] == []


def test_slots_invalid_date(client, seed):
    resp = client.get('/doctors/1/slots?date=01-09-2025')
    assert resp.status_code == 400
    assert 'Invalid date format' in resp.get_json()['error']


def test_slots_unknown_doctor(client, seed):
    assert client.get('/doctors/99/slots').status_code == 404


def test_slots_include_due_date_field(client, seed):
    seed(1, 1, 0)
    slot = client.get('/doctors/1/slots').get_json()['data']['booked_slots'][0]
    assert 'due_date' in slot and slot['due_date'] is None
