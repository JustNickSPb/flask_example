import random

import factory

from module_29_testing.hw.main.models import Client, db, Parking


class ClientFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Client
        sqlalchemy_session = db.session

    name = factory.Faker('first_name')
    surname = factory.Faker('last_name')
    credit_card = factory.Faker('credit_card_number')
    car_number = factory.Faker('license_plate')

    def to_json(self):
        return {'name': self.name,
                'surname': self.surname,
                'credit_card': self.credit_card,
                'car_number': self.car_number}


class ParkingFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Parking
        sqlalchemy_session = db.session

    address = factory.Faker('address')
    opened = True
    count_places = factory.LazyAttribute(lambda i: random.randint(1, 100))
    count_available_places = count_places

    def to_json(self):
        return {'address': self.address,
                'opened': self.opened,
                'count_places': self.count_places,
                'count_available_places': self.count_available_places}