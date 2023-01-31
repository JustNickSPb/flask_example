import datetime
import time

import pytest

from module_29_testing.hw.main.app import create_app, db as _db
from module_29_testing.hw.main.models import Client, Parking, ClientParking


@pytest.fixture
def app():
    _app = create_app()
    _app.config['TESTING'] = True
    _app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

    with _app.app_context():
        _db.create_all()
        client = Client(name='name',
                        surname='surname',
                        credit_card='1234 1234 1234 1234',
                        car_number='A123AA123')
        client_2 = Client(name='Another name',
                        surname='One mor client',
                        credit_card='2344 5673 8909 8765',
                        car_number='T456HC234')
        parking = Parking(address='address',
                          opened=True,
                          count_places=2,
                          count_available_places=1)
        parking_log = ClientParking(client_id=2,
                                    parking_id=1,
                                    time_in=datetime.datetime.now())
        _db.session.add_all([client, client_2, parking, parking_log])
        _db.session.commit()

        yield _app

        _db.session.close()
        _db.drop_all()


@pytest.fixture
def client(app):
    client = app.test_client()
    yield client


@pytest.fixture
def db(app):
    with app.app_context():
        yield _db
