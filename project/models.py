import psycopg2

# подключаемся к БД
con = psycopg2.connect(
    dbname='cosmetics_store_db',
    user='postgres',
    password='123456789',
    host='localhost',
    port=5432
)

#  создаем экземпляр курсора, который непосредственно выполняет запросы
cur = con.cursor()

# выполняем создание таблицы
cur.execute("CREATE TABLE mail_user(id serial, name varchar(50), email varchar(100) PRIMARY KEY NOT NULL, password varchar, role varchar(20))")
con.commit()
cur.execute("CREATE TABLE product(id serial, name varchar(255), description varchar(1000), price real, category integer, image varchar, brand varchar, country integer)")
con.commit()
cur.execute("CREATE TABLE category(id serial, name varchar)")
con.commit()
cur.execute("CREATE TABLE country(id serial, name varchar)")
con.commit()
cur.execute("CREATE TABLE brand(id serial, name varchar, description varchar)")
con.commit()
cur.execute("CREATE TABLE user_order(id serial, mail_user varchar, order_data date, total_price real, product integer)")
con.commit()
# закрываем подключение к БД
cur.close()
con.close()
