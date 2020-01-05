import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import *
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

## ROUTES
'''
@TODO implement endpoint
  GET /drinks
    it should be a public endpoint
    it should contain only the drink.short() data representation
  returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''
#  GET Drinks (short representation)
#  ----------------------------------------------------------------
@app.route('/drinks')
def get_drinks():
  try:
    # Return all drinks formatted in the drink.short() data representation
    return jsonify({
      'success': True,
      'drinks': list(map(Drink.short, Drink.query.all()))
    })
  except:
    abort(422)

'''
@TODO implement endpoint
  GET /drinks-detail
    it should require the 'get:drinks-detail' permission
    it should contain the drink.long() data representation
  returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''

#  GET Drinks (long representation)
#  ----------------------------------------------------------------
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
  # Return all drinks formatted in the drink.long() data representation
  return jsonify({
    'success': True,
    'drinks': list(map(Drink.long, Drink.query.all()))
  })

'''
@TODO implement endpoint
  POST /drinks
    it should create a new row in the drinks table
    it should require the 'post:drinks' permission
    it should contain the drink.long() data representation
  returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
    or appropriate status code indicating reason for failure
'''

#  POST Drink
#  ----------------------------------------------------------------
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt):
  body = request.json
  title = body.get('title', None)
  recipe = body.get('recipe', None)

  # Abort 400 if the title in the request matches any of the currently saved drink titles
  if title in list(map(Drink.get_title, Drink.query.all())):
    abort(400, 'This title is already taken. Please provide a new title and try again.')

  # Abort 400 if any fields are missing
  if any(arg is None for arg in [title, recipe]) or '' in [title, recipe]:
    abort(400, 'title and recipe are required fields.')

  # Create and insert a new drink
  new_drink = Drink(title=title, recipe=json.dumps(recipe))
  new_drink.insert()

  # Return the newly created drink in the drink.long() data representation
  return jsonify({
    'success': True,
    'drinks': [Drink.query.get(new_drink.id).long()]
  })

'''
@TODO implement endpoint
  PATCH /drinks/<id>
    where <id> is the existing model id
    it should respond with a 404 error if <id> is not found
    it should update the corresponding row for <id>
    it should require the 'patch:drinks' permission
    it should contain the drink.long() data representation
  returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
    or appropriate status code indicating reason for failure
'''

#  PATCH Drinks
#  ----------------------------------------------------------------
@app.route('/drinks/<drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, drink_id):
  drink = Drink.query.get(drink_id)

  # Abort 404 if the drink was not found
  if drink is None:
    abort(404)

  body = request.json
  title = body.get('title', None)
  recipe = body.get('recipe', None)

  # Abort 400 if any fields are missing
  if any(arg is None for arg in [title, recipe]) or '' in [title, recipe]:
    abort(400, 'title and recipe are required fields.')

  # Update the drink with the new title and/or recipe
  drink.title = title
  drink.recipe = json.dumps(recipe) # Convert JSON object to string
  drink.update()

  # Return the updated drink in the drink.long() data representation
  return jsonify({
    'success': True,
    'drinks': [Drink.query.get(drink_id).long()]
  })

'''
@TODO implement endpoint
  DELETE /drinks/<id>
    where <id> is the existing model id
    it should respond with a 404 error if <id> is not found
    it should delete the corresponding row for <id>
    it should require the 'delete:drinks' permission
  returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
    or appropriate status code indicating reason for failure
'''

#  DELETE Drinks
#  ----------------------------------------------------------------
@app.route('/drinks/<drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, drink_id):
  drink = Drink.query.get(drink_id)

  # Abort 404 if the drink was not found
  if drink is None:
    abort(404)

  # Delete the drink
  drink.delete()

  return jsonify({
    'success': True,
    'delete': drink_id
  })

## ERROR HANDLING

# Unprocessable Entity
@app.errorhandler(422)
def unprocessable(error):
  return jsonify({
    "success": False, 
    "error": 422,
    "message": "Unable to process your request. Please try again later."
  }), 422

# Not Found
@app.errorhandler(404)
def not_found_error(error):
  return jsonify({
    "success": False, 
    "error": 404,
    "message": "Resource not found."
  }), 404

# Bad Request
@app.errorhandler(400)
def bad_request(error):
  return jsonify({
    "success": False, 
    "error": 400,
    "message": str(error)
  }), 400

# AuthError exceptions raised by the @requires_auth(permission) decorator method
@app.errorhandler(AuthError)
def auth_error(auth_error):
  return jsonify({
    "success": False,
    "error": auth_error.status_code,
    "message": auth_error.error['description']
  }), auth_error.status_code
