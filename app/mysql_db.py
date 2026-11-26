"""Parameterized MySQL adapter for the XAMPP deployment."""
import pymysql
from pymysql.cursors import DictCursor
from pymysql.constants import FIELD_TYPE

class MySQLDatabase:
    def __init__(self, config):
        converters=pymysql.converters.conversions.copy()
        converters[FIELD_TYPE.TIMESTAMP]=str
        converters[FIELD_TYPE.DATETIME]=str
        self.connection=pymysql.connect(conv=converters,host=config['DB_HOST'],port=int(config['DB_PORT']),user=config['DB_USER'],password=config['DB_PASSWORD'],database=config['DB_NAME'],charset='utf8mb4',cursorclass=DictCursor,autocommit=False,connect_timeout=5)
    def execute(self, sql, params=()):
        sql=sql.replace('INSERT OR IGNORE','INSERT IGNORE')
        if params:sql=sql.replace('%','%%').replace('?','%s')
        cursor=self.connection.cursor()
        cursor.execute(sql,params or None)
        return cursor
    def executescript(self, sql):
        for statement in sql.split(';'):
            if statement.strip():
                with self.connection.cursor() as cursor:cursor.execute(statement)
    def commit(self):self.connection.commit()
    def close(self):self.connection.close()
