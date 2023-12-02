#!/usr/bin/python3
"""
API endpoints for Place objects.
"""
from flask import abort, jsonify, request
from api.v1.views import app_views
from models import storage
from models.place import Place
from models.city import City
from models.user import User
from models.state import State
from models.city import City
from models.amenity import Amenity


@app_views.route('/cities/<city_id>/places',
                 methods=['GET'],
                 strict_slashes=False)
def get_places_by_city(city_id):
    """Retrieve the list of all Place objects of a City."""
    if city_id is None:
        abort(404)
    city = storage.get(City, city_id)
    if city is None:
        abort(404)
    places = [place.to_dict() for place in city.places]
    return jsonify(places)


@app_views.route('/places/<place_id>', methods=['GET'], strict_slashes=False)
def get_place(place_id):
    """Retrieve a Place object by place_id."""
    place = storage.get(Place, place_id)
    if place is None:
        abort(404)
    return jsonify(place.to_dict())


@app_views.route('/places/<place_id>',
                 methods=['DELETE'],
                 strict_slashes=False)
def delete_place(place_id):
    """Delete a Place object by place_id."""
    place = storage.get(Place, place_id)
    if place is None:
        abort(404)
    storage.delete(place)
    storage.save()
    return jsonify({}), 200


@app_views.route('/cities/<city_id>/places',
                 methods=['POST'],
                 strict_slashes=False)
def create_place(city_id):
    """Create a new Place."""
    if city_id is None:
        abort(404)
    city = storage.get(City, city_id)
    if city is None:
        abort(404)

    data = request.get_json()
    if data is None:
        abort(400, 'Not a JSON')
    if 'user_id' not in data:
        abort(400, 'Missing user_id')
    if 'name' not in data:
        abort(400, 'Missing name')

    user = storage.get(User, data['user_id'])
    if user is None:
        abort(404)

    new_place = Place(city_id=city_id, **data)
    new_place.save()

    return jsonify(new_place.to_dict()), 201


@app_views.route('/places/<place_id>', methods=['PUT'], strict_slashes=False)
def update_place(place_id):
    """Update a Place object by place_id."""
    place = storage.get(Place, place_id)
    if place is None:
        abort(404)

    data = request.get_json()
    if data is None:
        abort(400, 'Not a JSON')

    # Ignore keys: id, user_id, city_id, created_at, and updated_at
    keys_to_ignore = ['id', 'user_id', 'city_id', 'created_at', 'updated_at']
    for key, value in data.items():
        if key not in keys_to_ignore:
            setattr(place, key, value)

    place.save()

    return jsonify(place.to_dict()), 200


@app_views.route('/places_search', methods=['POST'], strict_slashes=False)
def places_search():
    """Retrieves all Place objects depending of the JSON
    in the body of the request
    """
    data = request.get_json()
    if not data:
        places = storage.all(Place).values()
    else:
        places = set()

        states = data.get('states', [])
        cities = data.get('cities', [])
        amenities = data.get('amenities', [])

        for state_id in states:
            state = storage.get(State, state_id)
            if state:
                places.update(state.places)

        for city_id in set(cities + [city_id for state_id in states
                           for city_id in
                           storage.get(State, state_id).cities]):
            city = storage.get(City, city_id)
            if city:
                places.update(city.places)

        places = [place for place in places if
                  all(amenity_id in place.amenities_ids
                      for amenity_id in amenities)]

    res = [place.to_dict() for place in places]
    return jsonify(res)
