import psycopg2
from secret import *


class Database:
    def __init__(self):
        self.con = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host='localhost',
            port=5432
        )
        self.cur = self.con.cursor()

    def select(self, query):
        self.cur.execute(query)
        data = self.prepare_data(self.cur.fetchall())
        try:
            if len(data) == 1:
                data = data[0]
        except:
            return 0

        return data

    def insert(self, query):
        self.cur.execute(query)
        self.con.commit()

    def prepare_data(self, data):
        films = []
        if len(data):
            column_names = [desc[0] for desc in self.cur.description]
            for row in data:
                films += [{c_name: row[key] for key, c_name in enumerate(column_names)}]

            return films

    def update(self, query):
        self.cur.execute(query)
        self.con.commit()

    def delete(self, query):
        self.cur.execute(query)
        self.con.commit()
