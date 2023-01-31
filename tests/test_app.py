import time

import pytest

from module_29_testing.hw.main.models import Parking


@pytest.mark.parametrize('route', ['/clients', '/clients/1'])
def test_all_get_return_200(client, route):
    response = client.get(route)
    assert response.status_code == 200


def test_create_client(client):
    client_to_create = {'name': 'test',
                        'surname': 'test',
                        'car_number': 'test',
                        'credit_card': 'test'}
    added_client = client.post('/clients', json=client_to_create)

    assert added_client.status_code == 201
    assert added_client.json['success'] == True
    added_client_json = added_client.json['added_client']
    del added_client_json['id']
    assert added_client_json == client_to_create

def test_cannot_create_client_without_name(client):
    client_to_create = {'surname': 'test',
                        'car_number': 'test',
                        'credit_card': 'test'}
    added_client = client.post('/clients', json=client_to_create)

    assert added_client.status_code == 400
    assert added_client.json['success'] == False
    assert added_client.json['reason'] == 'Client has to have name'


def test_cannot_create_client_without_surname(client):
    client_to_create = {'name': 'test',
                        'car_number': 'test',
                        'credit_card': 'test'}
    added_client = client.post('/clients', json=client_to_create)

    assert added_client.status_code == 400
    assert added_client.json['success'] == False
    assert added_client.json['reason'] == 'Client has to have surname'


def test_create_parking(client):
    parking = {'address': 'test',
               'count_places': 10}
    added_parking = client.post('/parkings', json=parking)

    assert added_parking.status_code == 201
    assert added_parking.json['success'] == True
    added_parking_json = added_parking.json['added_parking_zone']
    del added_parking_json['opened']
    del added_parking_json['id']
    parking['count_available_places'] = 10
    assert added_parking_json == parking


def test_cannot_create_parking_without_address(client):
    parking = {'count_places': 10}
    added_parking = client.post('/parkings', json=parking)

    assert added_parking.status_code == 400
    assert added_parking.json['success'] == False
    assert added_parking.json['reason'] == 'Parking has to have address'


def test_cannot_create_parking_without_lots(client):
    parking = {'address': 'test'}
    added_parking = client.post('/parkings', json=parking)

    assert added_parking.status_code == 400
    assert added_parking.json['success'] == False
    assert added_parking.json['reason'] == 'Parking has to have parking lots'


def test_cannot_create_same_parking_twice(client):
    parking = {'address': 'test_address',
               'count_places': 10}
    added_parking = client.post('/parkings', json=parking)
    assert added_parking.status_code == 201
    added_parking = client.post('/parkings', json=parking)

    assert added_parking.status_code == 400
    assert added_parking.json['success'] == False
    assert added_parking.json['reason'] == 'Already have parking with such address'


@pytest.mark.parking
def test_enter_parking(client):
    parking_request = {'client_id': 1,
                       'parking_id': 1}
    enter_parking_req = client.post('/client_parkings', json=parking_request)

    assert enter_parking_req.status_code == 201
    assert enter_parking_req.json['success'] == True
    assert enter_parking_req.json['parking_log']['client_id'] == parking_request['client_id']
    assert enter_parking_req.json['parking_log']['parking_id'] == parking_request['parking_id']
    assert enter_parking_req.json['parking_log']['time_in']
    assert not enter_parking_req.json['parking_log']['time_out']


@pytest.mark.parking
def test_cannot_enter_parking_when_closed(client):
    parking = client.post('/parkings', json={'address': 'some_address',
                                             'count_places': 1,
                                             'opened': False})
    assert parking.status_code == 201
    parking_id = parking.json['added_parking_zone']['id']
    parking_request = {'client_id': 1,
                       'parking_id': parking_id}
    enter_parking_req = client.post('/client_parkings', json=parking_request)

    assert enter_parking_req.status_code == 409
    assert enter_parking_req.json['success'] == False
    assert enter_parking_req.json['reason'] == 'Parking is closed'


@pytest.mark.parking
def test_cannot_enter_parking_when_full(client):
    new_client = client.post('/clients', json={'name': 'some_name',
                                               'surname': 'surname',
                                               'car_number': 'car_number'})
    assert new_client.status_code == 201
    first_enter = client.post('/client_parkings', json={'client_id': 1,
                                                        'parking_id': 1})
    assert first_enter.status_code == 201
    new_enter = client.post('/client_parkings', json={'client_id': 2,
                                                      'parking_id': 1})

    assert new_enter.status_code == 409
    assert new_enter.json['success'] == False
    assert new_enter.json['reason'] == 'Parking is full'


@pytest.mark.parking
def test_cannot_enter_non_existent_parking(client):
    enter = client.post('/client_parkings', json={'client_id': 1,
                                                  'parking_id': 42})

    assert enter.status_code == 404
    assert enter.json['success'] == False
    assert enter.json['reason'] == 'Parking doesn\'t exist'


@pytest.mark.parking
def test_not_given_parking_id_when_trying_to_enter_parking(client):
    enter = client.post('/client_parkings', json={'client_id': 1})

    assert enter.status_code == 400
    assert enter.json['success'] == False
    assert enter.json['reason'] == 'Need to specify "parking_id" parameter'


@pytest.mark.parking
def test_cannot_enter_parking_non_existent_client(client):
    enter = client.post('/client_parkings', json={'client_id': 42,
                                                  'parking_id': 1})

    assert enter.status_code == 404
    assert enter.json['success'] == False
    assert enter.json['reason'] == 'Client doesn\'t exist'


@pytest.mark.parking
def test_not_given_client_id_when_trying_to_enter_parking(client):
    enter = client.post('/client_parkings', json={'parking_id': 1})

    assert enter.status_code == 400
    assert enter.json['success'] == False
    assert enter.json['reason'] == 'Need to specify "client_id" parameter'


@pytest.mark.parking
def test_cannot_enter_twice(client):
    new_parking = client.post('/parkings', json={'address': 'new address',
                                                 'count_places': 2})
    assert new_parking.status_code == 201
    enter_request = {'client_id': 1,
                     'parking_id': new_parking.json['added_parking_zone']['id']}
    first_enter = client.post('/client_parkings', json=enter_request)
    assert first_enter.status_code == 201
    second_enter = client.post('/client_parkings', json=enter_request)

    assert second_enter.status_code == 409
    assert second_enter.json['success'] == False
    assert second_enter.json['reason'] == 'This client is already at this parking'


@pytest.mark.parking
def test_cannot_enter_without_car(client):
    new_client = client.post('/clients', json={'name': 'name',
                                               'surname': 'surname'})
    assert new_client.status_code == 201
    enter = client.post('/client_parkings',
                        json={'client_id': new_client.json['added_client']['id'],
                              'parking_id': 1})

    assert enter.status_code == 409
    assert enter.json['success'] == False
    assert enter.json['reason'] == 'Cannot enter parking without car'


@pytest.mark.parking
def test_available_places_reducing_when_enter_parking(client, db):
    parking = db.session.query(Parking).get(1)
    initial_places = parking.count_available_places

    enter = client.post('/client_parkings', json={'client_id': 1,
                                                  'parking_id': 1})
    assert enter.status_code == 201
    assert parking.count_available_places < initial_places


@pytest.mark.parking
def test_available_places_increasing_when_leave_parking(client, db):
    parking = db.session.query(Parking).get(1)
    initial_places = parking.count_available_places

    leave = client.delete('/client_parkings', json={'client_id': 2,
                                                  'parking_id': 1})
    assert leave.status_code == 200

    assert parking.count_available_places > initial_places


@pytest.mark.parking
def test_time_out_bigger_than_time_in(client):
    time.sleep(1)
    leave = client.delete('/client_parkings', json={'client_id': 2,
                                                    'parking_id': 1})
    assert leave.status_code == 200

    assert leave.json['parking_log']['time_out'] > leave.json['parking_log']['time_in']


@pytest.mark.parking
def test_leave_parking(client):
    leave = client.delete('/client_parkings', json={'client_id': 2,
                                                    'parking_id': 1})

    assert leave.status_code == 200
    assert leave.json['success'] == True
    assert leave.json['parking_log']['time_out']


@pytest.mark.parking
def test_cannot_leave_parking_when_not_entered(client):
    leave = client.delete('/client_parkings', json={'client_id': 1,
                                                    'parking_id': 1})

    assert leave.status_code == 404
    assert leave.json['success'] == False
    assert leave.json['reason'] == 'Cannot find parking log'


@pytest.mark.parking
def test_cannot_leave_parking_without_credit_card(client):
    new_client = client.post('/clients', json={'name': 'test',
                                               'surname': 'test',
                                               'car_number': 'car_num'})
    assert new_client.status_code == 201
    enter = client.post('/client_parkings',
                        json={'client_id': new_client.json['added_client']['id'],
                              'parking_id': 1})
    assert enter.status_code == 201
    leave = client.delete('/client_parkings',
                          json={'client_id': new_client.json['added_client']['id'],
                                'parking_id': 1})

    assert leave.status_code == 402
    assert leave.json['success'] == False
    assert leave.json['reason'] == 'No credit card added, cannot process payment'


@pytest.mark.parking
def test_cannot_leave_without_client_id_provided(client):
    leave = client.delete('/client_parkings', json={'parking_id': 1})

    assert leave.status_code == 400
    assert leave.json['success'] == False
    assert leave.json['reason'] == 'Need to specify client_id'


@pytest.mark.parking
def test_cannot_leave_without_parking_id_provided(client):
    leave = client.delete('/client_parkings', json={'client_id': 1})

    assert leave.status_code == 400
    assert leave.json['success'] == False
    assert leave.json['reason'] == 'Need to specify parking_id'
