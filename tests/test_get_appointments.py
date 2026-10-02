def test_empty_list(client):
    resp = client.get('/appointments')
    assert resp.status_code == 200
    assert resp.get_json() == {'data': [], 'error': None, 'status': 200}


def test_response_shape_and_doctor_name(client, seed):
    seed(1, 1, 0)
    body = client.get('/appointments').get_json()
    assert set(body) == {'data', 'error', 'status'}
    assert body['error'] is None and body['status'] == 200
    item = body['data'][0]
    assert item['doctor_name'] == 'Dr Alpha'
    assert {'id', 'patient_id', 'doctor_id', 'start_time', 'end_time',
            'reason', 'status'} <= set(item)


def test_doctor_name_matches_each_doctor(client, seed):
    seed(1, 1, 0)
    seed(1, 2, 1)
    names = {a['doctor_id']: a['doctor_name'] for a in client.get('/appointments').get_json()['data']}
    assert names == {1: 'Dr Alpha', 2: 'Dr Beta'}


def test_filter_by_patient_id(client, seed):
    seed(1, 1, 0)
    seed(2, 1, 1)
    data = client.get('/appointments?patient_id=2').get_json()['data']
    assert len(data) == 1 and data[0]['patient_id'] == 2


def test_filter_by_doctor_id(client, seed):
    seed(1, 1, 0)
    seed(1, 2, 1)
    data = client.get('/appointments?doctor_id=2').get_json()['data']
    assert len(data) == 1 and data[0]['doctor_id'] == 2


def test_filter_by_patient_and_doctor(client, seed):
    seed(1, 1, 0)
    seed(1, 2, 1)
    seed(2, 2, 2)
    data = client.get('/appointments?patient_id=1&doctor_id=2').get_json()['data']
    assert len(data) == 1
    assert (data[0]['patient_id'], data[0]['doctor_id']) == (1, 2)


def test_filter_with_no_match(client, seed):
    seed(1, 1, 0)
    assert client.get('/appointments?patient_id=99').get_json()['data'] == []


def test_query_count_does_not_grow_with_appointments(client, seed, count_queries):
    """Regression test for the N+1 on doctor_name."""
    seed(1, 1, 0)
    with count_queries() as small:
        client.get('/appointments')
    for slot in range(1, 21):
        seed(1, 1 + slot % 2, slot)
    with count_queries() as large:
        client.get('/appointments')
    assert len(small) == len(large) == 1
