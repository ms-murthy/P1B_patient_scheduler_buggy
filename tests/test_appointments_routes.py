VALID = {'patient_id': 1, 'doctor_id': 1,
         'start_time': '2025-09-01T09:00:00', 'end_time': '2025-09-01T09:30:00'}


# ---- GET /appointments/<id> -------------------------------------------------

def test_get_single_appointment(client, seed):
    appt = seed(1, 1, 0)
    resp = client.get(f'/appointments/{appt.id}')
    assert resp.status_code == 200
    data = resp.get_json()['data']
    assert data['id'] == appt.id and data['due_date'] is None


def test_get_single_appointment_not_found(client, seed):
    resp = client.get('/appointments/999')
    assert resp.status_code == 404
    assert resp.get_json() == {'data': None, 'error': 'Appointment not found', 'status': 404}


# ---- POST /appointments -----------------------------------------------------

def test_create_appointment_success(client, seed):
    resp = client.post('/appointments', json={**VALID, 'reason': 'Check-up'})
    assert resp.status_code == 201
    data = resp.get_json()['data']
    assert data['status'] == 'scheduled' and data['reason'] == 'Check-up'
    assert data['start_time'] == '2025-09-01T09:00:00'


def test_create_defaults_reason_to_empty(client, seed):
    assert client.post('/appointments', json=VALID).get_json()['data']['reason'] == ''


def test_create_empty_body(client, seed):
    resp = client.post('/appointments', json={})
    assert resp.status_code == 400
    assert resp.get_json()['error'] == 'No data provided'


def test_create_missing_each_required_field(client, seed):
    for field in ('patient_id', 'doctor_id', 'start_time', 'end_time'):
        body = {k: v for k, v in VALID.items() if k != field}
        resp = client.post('/appointments', json=body)
        assert resp.status_code == 400, field
        assert resp.get_json()['error'] == f'Missing field: {field}'


def test_create_invalid_datetime(client, seed):
    resp = client.post('/appointments', json={**VALID, 'start_time': 'tomorrow'})
    assert resp.status_code == 400
    assert 'ISO 8601' in resp.get_json()['error']


def test_create_end_before_start(client, seed):
    resp = client.post('/appointments', json={**VALID, 'end_time': '2025-09-01T08:00:00'})
    assert resp.status_code == 400


def test_create_end_equal_start(client, seed):
    resp = client.post('/appointments', json={**VALID, 'end_time': VALID['start_time']})
    assert resp.status_code == 400


def test_create_conflict_returns_409(client, seed):
    seed(2, 1, 0)
    resp = client.post('/appointments', json=VALID)
    assert resp.status_code == 409
    assert resp.get_json()['data'] is None


def test_create_back_to_back_allowed(client, seed):
    seed(2, 1, 0)  # 09:00-09:30
    resp = client.post('/appointments', json={**VALID, 'start_time': '2025-09-01T09:30:00',
                                              'end_time': '2025-09-01T10:00:00'})
    assert resp.status_code == 201


def test_create_same_time_other_doctor_allowed(client, seed):
    seed(2, 1, 0)
    assert client.post('/appointments', json={**VALID, 'doctor_id': 2}).status_code == 201


def test_create_persists(client, seed):
    created = client.post('/appointments', json=VALID).get_json()['data']
    fetched = client.get(f"/appointments/{created['id']}").get_json()['data']
    assert fetched == created


# ---- PUT /appointments/<id> (reschedule) -----------------------------------

def test_reschedule_success(client, seed):
    appt = seed(1, 1, 0)
    resp = client.put(f'/appointments/{appt.id}', json={
        'start_time': '2025-09-02T14:00:00', 'end_time': '2025-09-02T14:30:00'})
    assert resp.status_code == 200
    assert resp.get_json()['data']['start_time'] == '2025-09-02T14:00:00'


def test_reschedule_not_found(client, seed):
    resp = client.put('/appointments/999', json={
        'start_time': '2025-09-02T14:00:00', 'end_time': '2025-09-02T14:30:00'})
    assert resp.status_code == 404


def test_reschedule_missing_fields(client, seed):
    appt = seed(1, 1, 0)
    assert client.put(f'/appointments/{appt.id}', json={'start_time': '2025-09-02T14:00:00'}).status_code == 400


def test_reschedule_invalid_datetime(client, seed):
    appt = seed(1, 1, 0)
    resp = client.put(f'/appointments/{appt.id}', json={'start_time': 'x', 'end_time': 'y'})
    assert resp.status_code == 400


def test_reschedule_conflict_with_other_appointment(client, seed):
    appt = seed(1, 1, 0)   # 09:00
    seed(2, 1, 1)          # 10:00
    resp = client.put(f'/appointments/{appt.id}', json={
        'start_time': '2025-09-01T10:00:00', 'end_time': '2025-09-01T10:30:00'})
    assert resp.status_code == 409


def test_reschedule_overlapping_own_old_slot_allowed(client, seed):
    appt = seed(1, 1, 0)   # 09:00-09:30
    resp = client.put(f'/appointments/{appt.id}', json={
        'start_time': '2025-09-01T09:15:00', 'end_time': '2025-09-01T09:45:00'})
    assert resp.status_code == 200


def test_reschedule_back_to_back_allowed(client, seed):
    appt = seed(1, 1, 0)
    seed(2, 1, 1)          # 10:00-10:30
    resp = client.put(f'/appointments/{appt.id}', json={
        'start_time': '2025-09-01T09:30:00', 'end_time': '2025-09-01T10:00:00'})
    assert resp.status_code == 200


def test_reschedule_keeps_due_date(client, seed):
    created = client.post('/appointments', json={**VALID, 'due_date': '2025-09-15T12:00:00'}).get_json()['data']
    resp = client.put(f"/appointments/{created['id']}", json={
        'start_time': '2025-09-02T14:00:00', 'end_time': '2025-09-02T14:30:00'})
    assert resp.get_json()['data']['due_date'] == '2025-09-15T12:00:00'


# ---- DELETE /appointments/<id> (cancel) ------------------------------------

def test_cancel_is_soft_delete(client, seed):
    appt = seed(1, 1, 0)
    resp = client.delete(f'/appointments/{appt.id}')
    assert resp.status_code == 200
    assert resp.get_json()['data'] == {'id': appt.id, 'status': 'cancelled'}
    assert client.get(f'/appointments/{appt.id}').get_json()['data']['status'] == 'cancelled'


def test_cancel_not_found(client, seed):
    assert client.delete('/appointments/999').status_code == 404


def test_cancel_frees_the_slot(client, seed):
    appt = seed(2, 1, 0)
    client.delete(f'/appointments/{appt.id}')
    assert client.post('/appointments', json=VALID).status_code == 201
