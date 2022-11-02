import psycopg2

class Database:
    def __init__(self):
        # Соединение с СУБД
        self.con = psycopg2.connect(
            dbname='cosmetics_store_db',
            user='postgres',
            password='123456789',
            host='localhost',
            port=5432
        )
        # Взаимодействие с базой осуществляется при помощи отдельного класса, cursor
        self.cur = self.con.cursor()

    # заполнение таблицы
    def select(self, query):
        self.cur.execute(query)
        # позволяет извлечь все (оставшиеся) строки результата запроса, возвращая их в виде последовательности последовательностей
        data = self.prepare_data(self.cur.fetchall())
        try:
            if len(data) == 1:
                data = data[0]
        except:
            return 0

        return data

    def insert(self, query):
        self.cur.execute(query)
        # позволяет извлечь все (оставшиеся) строки результата запроса, возвращая их в виде последовательности последовательностей
        # data = self.prepare_data(self.cur.fetchall())
        # if len(data) == 1:
        #     data = data[0]
        self.con.commit()
        # return data

    def prepare_data(self, data):
        films = []
        if len(data):
            column_names = [desc[0] for desc in self.cur.description]
            for row in data:
                films += [{c_name: row[key] for key, c_name in enumerate(column_names)}]

            return films
