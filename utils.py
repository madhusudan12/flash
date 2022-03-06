
import logging

from sqlalchemy.types import *
from sqlalchemy import Table, Column, ForeignKeyConstraint

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

json_to_sql_alchemy_map = {
    "string": String,
    "integer": Integer,
    "long": BigInteger,
    "float": Float,
    "number": Float,
    "boolean": Boolean,
    "date": Date,
    "datetime": DateTime,
    "time": Time,
    "array": ARRAY,
    "any": String,
    "text": Text
}


def get_columns_from_json(json_data, primary_key):
    """
    Get the columns from the json data
    """
    columns = []
    for field in json_data:
        if field.get("name") == primary_key:
            columns.append(Column(field.get("name"), json_to_sql_alchemy_map.get(field['type'], String), primary_key=True))
        else:
            columns.append(Column(field['name'], json_to_sql_alchemy_map.get(field['type'], String)))
    columns.append(ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE', onupdate='CASCADE'))
    return columns


def create_table(table_name, primary_key, json_data, metadata):
    """
    Create the table from the json data
    """
    columns = get_columns_from_json(json_data, primary_key)
    table = Table(table_name, metadata, *columns)
    log.info(f"Creating table {table_name} with primary key : {primary_key} and schema {json_data}")
    resp = table.create()
    log.info(f"Table {table_name} created successfully")
    return resp


    
