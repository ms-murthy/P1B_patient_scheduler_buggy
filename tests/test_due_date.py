BASE = {'patient_id': 1, 'doctor_id': 1,
        'start_time': '2025-09-01T09:00:00', 'end_time': '2025-09-01T09:30:00'}


def test_create_without_due_date(client, seed):
    seed(2, 2, 10)
    resp = client.post('/appointments', json=BASE)
    assert resp.status_code == 201
    assert resp.get_json()['data']['due_date'] is None


def test_create_with_due_date(client, seed):
    seed(2, 2, 10)
    resp = client.post('/appointments', json={**BASE, 'due_date': '2025-09-15T12:00:00'})
    assert resp.status_code == 201
    assert resp.get_json()['data']['due_date'] == '2025-09-15T12:00:00'


def test_due_date_returned_by_list(client, seed):
    seed(2, 2, 10)
    client.post('/appointments', json={**BASE, 'due_date': '2025-09-15T12:00:00'})
    data = client.get('/appointments?patient_id=1').get_json()['data']
    assert data[0]['due_date'] == '2025-09-15T12:00:00'


def test_invalid_due_date_rejected(client, seed):
    seed(2, 2, 10)
    resp = client.post('/appointments', json={**BASE, 'due_date': 'not-a-date'})
    assert resp.status_code == 400
    assert 'due_date' in resp.get_json()['error']


def test_non_string_due_date_rejected(client, seed):
    seed(2, 2, 10)
    assert client.post('/appointments', json={**BASE, 'due_date': 123}).status_code == 400
