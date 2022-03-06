
import jwt
from functools import wraps

from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy


from application import app


db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    public_id = db.Column(db.String(128), unique = True)
    name = db.Column(db.String(128))
    username = db.Column(db.String(256), unique = True)
    password = db.Column(db.String(1024))
  

def auth_required(fun):
    @wraps(fun)
    def decorater(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message' : 'Token is missing !!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            user = User.query.filter_by(public_id = data['public_id']).first()
        except:
            return jsonify({'message' : 'Invalid Acsess Token'}), 401
        return  fun(user, *args, **kwargs)
    return decorater
  
