import datetime

from flask import Flask, jsonify, request

from .models import db, Client, Parking, ClientParking


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prod.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    @app.route('/clients', methods=['GET'])
    def get_all_clients():
        clients = db.session.query(Client).all()
        client_list = [c.to_json() for c in clients]

        return jsonify(client_list), 200

    @app.route('/clients/<int:client_id>', methods=['GET'])
    def get_client_by_id(client_id):
        client = db.session.query(Client).filter(Client.id==client_id).first()

        return client.to_json(), 200

    @app.route('/clients', methods=['POST'])
    def new_client():
        data = request.json
        name = data.get('name')
        surname = data.get('surname')
        car_number = data.get('car_number')
        credit_card = data.get('credit_card')

        if not name:
            return jsonify(success=False,
                           reason='Client has to have name'), 400
        if not surname:
            return jsonify(success=False,
                           reason='Client has to have surname'), 400

        client = Client(name=name,
                        surname=surname,
                        car_number=car_number,
                        credit_card=credit_card)
        db.session.add(client)
        db.session.commit()

        return jsonify(success=True, added_client=client.to_json()), 201

    @app.route('/parkings', methods=['POST'])
    def new_parking_zone():
        data = request.json
        address = data.get('address')
        opened = data.get('opened', True)
        count_places = data.get('count_places')

        if not address:
            return jsonify(success=False,
                           reason='Parking has to have address'), 400
        parking_exists = db.session.query(Parking).filter(Parking.address==address).all()
        if len(parking_exists) > 0:
            return jsonify(success=False,
                           reason='Already have parking with such address'), 400
        if not count_places:
            return jsonify(success=False,
                           reason='Parking has to have parking lots'), 400

        parking = Parking(address=address,
                          opened=opened,
                          count_places=count_places,
                          count_available_places=count_places)
        db.session.add(parking)
        db.session.commit()

        return jsonify(success=True, added_parking_zone=parking.to_json()), 201

    @app.route('/client_parkings', methods=['POST'])
    def enter_parking():
        parking_request = request.json
        client_id = parking_request.get('client_id')
        parking_id = parking_request.get('parking_id')

        if not client_id:
            return jsonify(success=False,
                           reason='Need to specify "client_id" parameter'), 400
        if not parking_id:
            return jsonify(success=False,
                           reason='Need to specify "parking_id" parameter'), 400

        parking = db.session.query(Parking).get(parking_id)
        if not parking:
            return jsonify(success=False,
                           reason='Parking doesn\'t exist'), 404
        if not parking.opened:
            return jsonify(success=False, reason='Parking is closed'), 409
        if parking.count_available_places == 0:
            return jsonify(success=False, reason='Parking is full'), 409

        client = db.session.query(Client).get(client_id)
        if not client:
            return jsonify(success=False,
                           reason='Client doesn\'t exist'), 404
        if not client.car_number:
            return jsonify(success=False,
                           reason='Cannot enter parking without car'), 409

        client_on_parking = db.session.query(ClientParking)\
            .filter(ClientParking.client_id == client_id)\
            .filter(ClientParking.parking_id == parking_id)\
            .filter(ClientParking.time_out == None).all()
        if len(client_on_parking) > 0:
            return jsonify(success=False,
                           reason='This client is already at this parking'), 409

        parking.count_available_places -= 1
        parking_log = ClientParking(client_id=client_id,
                                    parking_id=parking_id,
                                    time_in=datetime.datetime.now())
        db.session.add(parking_log)
        db.session.commit()

        return jsonify(success=True, parking_log=parking_log.to_json()), 201


    @app.route('/client_parkings', methods=['DELETE'])
    def leave_parking():
        client_id = request.json.get('client_id')
        parking_id = request.json.get('parking_id')
        if not client_id:
            return jsonify(success=False,
                           reason='Need to specify client_id'), 400
        if not parking_id:
            return jsonify(success=False,
                           reason='Need to specify parking_id'), 400

        parking_log = db.session.query(ClientParking)\
            .filter(ClientParking.client_id==client_id)\
            .filter(ClientParking.parking_id==parking_id)\
            .filter(ClientParking.time_out==None)\
            .all()
        if len(parking_log) == 0:
            return jsonify(success=False,
                           reason='Cannot find parking log'), 404

        client = db.session.query(Client).get(client_id)
        if not client:
            return jsonify(success=False,
                           reason='Cannot find client with this client_id'), 404
        if not client.credit_card:
            return jsonify(success=False,
                           reason='No credit card added, cannot process payment'), 402

        parking = db.session.query(Parking).get(parking_id)
        parking.count_available_places += 1

        log_entry = parking_log[0]
        log_entry.time_out = datetime.datetime.now()
        db.session.commit()

        return jsonify(success=True, parking_log=log_entry.to_json()), 200


    return app