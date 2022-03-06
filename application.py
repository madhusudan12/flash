
from operator import index
import uuid
import logging
import json
from datetime import datetime, timedelta
import jwt

from flask import Flask, request, jsonify, Response
from  werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd


from sqlalchemy import create_engine, inspect
from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker

from utils import create_table


app = Flask(__name__)
app.config.from_object('config')


from user import User, auth_required,  db

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
metadata = MetaData(engine)
metadata.reflect()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)



    
@app.route("/")
@app.route("/ping")
def hello_world():
    return {"message": "pong"}




@app.route("/upload", methods=["POST"])
@auth_required
def upload(user):
    user_id = user.id
    files  = request.files.getlist("file[]")
    table_name = request.form.get("name") or request.form.get("instance")
    if not table_name:
        log.error("Table name is required")
        return jsonify({"message": "name or instance name is required"}), 400
    table_name = table_name.replace(" ", "_")
    table_name = f'{table_name}_{user_id}'
    table_name = table_name.lower()
    if files:
        schema_df = pd.read_csv(files[0], index_col=False)

        schema = json.loads(schema_df.to_json(orient="table"))
        schema_fields = schema['schema'].get('fields', [])
        schema_fields.append({"name": "user_id", "type": "integer"})
        schema_fields.append({"name": "filename", "type": "string"})
        primary_key = schema['schema'].get('primaryKey', None)
        if not primary_key:
            log.info("Primary key is not found, using id as primary key")
            schema_fields.append({"name": "id", "type": "integer"})
            primary_key = "id"
        if not schema_fields:
            log.error("Schema not found")
            return jsonify({"message": "file is empty"}), 400
        try:
            resp = create_table(table_name, primary_key, schema_fields, metadata)
        except Exception as e:
            log.exception(f"Error while creating table {table_name}")
            return jsonify({"message": "Error while creating table"}), 500
    log.info("loading data into table {}".format(table_name))
    schema_df['user_id'] = user_id
    schema_df['filename'] = files[0].filename
    log.info("Inserting data from file {} into table {}".format(files[0].filename, table_name))
    schema_df.to_sql(table_name, engine, if_exists="append", index=False, method="multi")
    try:
        for file in files[1:]:
            log.info("Inserting data from file {} into table {}".format(file.filename, table_name))
            df = pd.read_csv(file, index_col=False)
            df['user_id'] = user_id
            df['filename'] = file.filename
            df.to_sql(table_name, engine, if_exists="append", index=False, method="multi")
    except Exception as e:
        log.exception(f"Error while loading data into table {table_name}")
        return jsonify({"message": "Error while loading data into table"}), 500
    log.info("Data loaded successfully")
    return jsonify({"message": "upload success", "schema": schema_fields}), 200



@app.route("/download", methods=["GET"])
@auth_required
def download(user):
    user_id = user.id
    table_name = request.args.get("name") or request.args.get("instance")
    if not table_name:
        return jsonify({"message": "name or instance name is required"}), 400
    table_name = table_name.replace(" ", "_")
    table_name = f'{table_name}_{user_id}'
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"message": "filename is required"}), 400
    output_format = request.args.get("format") or "csv"
    if output_format not in ["csv", "json"]:
        return jsonify({"message": "format is required"}), 400
    insp = inspect(engine)
    log.info("Checking if table {} exists".format(table_name))
    is_table_exists = insp.has_table(table_name)
    if not is_table_exists:
        log.error("Table {} not found".format(table_name))
        return jsonify({"message": "Table not found"}), 400
    if not filename:
        return jsonify({"message": "filename is required"}), 400
    try:
        log.info("Fetching data from table {}".format(table_name))
        df = pd.read_sql_query(f"select * from {table_name} where user_id={user_id} and filename='{filename}'", engine)
        df.drop(columns=["user_id", "filename"], inplace=True)
        log.info("Data fetched successfully")
        if output_format == "csv":
            return Response(df.to_csv(index=False), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})
        else:
            return jsonify(df.to_json(orient="table"))
    except Exception as e:
        log.exception(f"Error while downloading data from table {table_name}")
        return jsonify({"message": "Error while downloading data from table"}), 500


@app.route('/login', methods =['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({'message' : 'username and password required'}), 400
    user = User.query.filter_by(username = auth.username).first() 
    if not user:
        return jsonify({'message': 'Could not verify'}), 401
    if check_password_hash(user.password, auth.password):
        token = jwt.encode({
            'public_id': user.public_id,
            'exp' : datetime.utcnow() + timedelta(minutes = 30)
        }, app.config['SECRET_KEY'])
  
        return jsonify({'token' : token.decode('UTF-8')}), 201
    return jsonify({'message': 'Could not verify'}), 401
  

@app.route('/signup', methods =['POST'])
def signup():
    data = request.json
    name, username = data.get('name'), data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username = username).first()
    if not user:
        user = User(
            public_id = str(uuid.uuid4()),
            name = name,
            username = username,
            password = generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'message':'Successfully registered.'}), 201
    else:
        return jsonify({'message':'User already exists. Create with different username'}), 202




if __name__ == "__main__":
    app.run()