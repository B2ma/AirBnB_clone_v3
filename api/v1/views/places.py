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
    """Search for Place objects based on JSON request."""
    try:
        search_data = request.get_json()
    except Exception as e:
        return jsonify({"error": "Not a JSON"}), 400

    if not search_data or all(len(v) == 0 for v in search_data.values()):
        places = storage.all("Place").values()
        return jsonify([place.to_dict() for place in places])

    places = set()

    # Filter by states
    if 'states' in search_data:
        for state_id in search_data['states']:
            state = storage.get("State", state_id)
            if state:
                places.update(state.cities)

    # Filter by cities
    if 'cities' in search_data:
        for city_id in search_data['cities']:
            city = storage.get("City", city_id)
            if city:
                places.add(city)

    # Filter by amenities
    if 'amenities' in search_data:
        amenities = {storage.get("Amenity", amenity_id) for amenity_id in search_data['amenities']}
        places = {place for place in places if amenities.issubset(place.amenities)}

    return jsonify([place.to_dict() for place in places])
