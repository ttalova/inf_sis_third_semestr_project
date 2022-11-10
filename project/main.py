from flask import Flask, redirect, url_for, render_template, request, make_response, session
import datetime
from db_util import Database
from werkzeug.security import generate_password_hash, check_password_hash

from help_function import *

app = Flask(__name__)
app.secret_key = '111'
# необходимо добавлять, чтобы время сессии не ограничивалось закрытием браузера
app.permanent_session_lifetime = datetime.timedelta(days=365)

# инициализация класса с методами для работы с БД
db = Database()


@app.route('/products', methods=['GET', 'POST'])
def index():
    session.setdefault('admin', False)
    session['no_user'] = {'favorites': [], 'shopping_cart': {}}
    products = db.select(f"SELECT * FROM product")
    search = ''
    categories = db.select(f"SELECT * FROM category")
    if isinstance(products, dict):
        products = [products]
    if isinstance(categories, dict):
        categories = [categories]
    if request.method == 'POST':
        search = request.form.get('search', '')
        category = request.form.get('category')
        if search:
            products = [product for product in products if
                        search.lower() in product['name'].lower() or search.lower() in product['description'].lower()]
        if category:
            products = [product for product in products if
                        int(category) == product['category']]
    if 'email' not in session:
        session['email'] = 'no_user'
        session[session['email']] = {'favorites': [], 'shopping_cart': {}}
        session_modified()
    user = user_logining()
    if products:
        quantity = [1] * len(products)
        products = zip(products, quantity)
    else:
        products = None
    context = {
        'products': products,
        'title': "Products",
        'exist': exist(),
        'user': user,
        'search': search,
        'categories': categories,
        'site': 'index',
        'admin': session['admin']
    }
    # возвращаем сгенерированный шаблон с нужным нам контекстом
    return render_template("index.html", **context)


@app.route("/products/<int:product_id>")
def get_product(product_id):
    # используем метод-обертку для выполнения запросов к БД
    product = db.select(f"SELECT * FROM product WHERE id = {product_id}")
    if len(product):
        content = {
            'title': product['name'],
            'product': product,
            'category': db.select(f"SELECT name FROM category WHERE id='{product['category']}'"),
            'country': db.select(f"SELECT name FROM country WHERE id='{product['country']}'"),
            'brand': db.select(f"SELECT name FROM brand WHERE id='{product['brand']}'"),
            'admin': session['admin'],

        }
        return render_template("product.html", **content)

    # если нужный фильм не найден, возвращаем шаблон с ошибкой
    return render_template("error.html", error="Такого товара не существует")


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    message = None
    if request.method == 'POST':
        user = db.select(f"SELECT * FROM mail_user WHERE mail_user.email = '{request.form.get('email')}'")
        if not user:
            password = generate_password_hash(request.form.get('password'))
            db.insert(
                f"INSERT INTO mail_user (name, gender, email, password, role) VALUES ('{request.form.get('name')}', '{request.form.get('gender')}', '{request.form.get('email')}', '{password}', 'user')")
            session['email'] = request.form.get('email')
            session[session['email']] = {'favorites': [], 'shopping_cart': {}}
            session.pop('no_user', None)
            session['admin'] = False
            return redirect(url_for("index"))
        else:
            message = 'Исправьте ошибки'
    user = user_logining()
    return render_template("signup.html", message=message, user=user)


@app.route("/login", methods=["POST", "GET"])
def login():
    message = None
    if request.method == "POST":
        user = db.select(f"SELECT * FROM mail_user WHERE mail_user.email = '{request.form.get('email')}'")
        if user and check_password_hash(user['password'], request.form.get('password')):
            session['email'] = request.form.get('email')  # чтение и обновление данных сессии
            if user['role'] == 'admin':
                session['admin'] = True
            if session['email'] not in session:
                session[session['email']] = {'favorites': [], 'shopping_cart': {}}
            if len(session['no_user']) != 0:
                session[session['email']]['favorites'] += session['no_user']['favorites']
                session[session['email']]['shopping_cart'].update(session['no_user']['shopping_cart'])
                session.pop('no_user', None)
            session_modified()
            return redirect(url_for("index"))
        else:
            message = 'Неправильный логин или пароль'
    user = user_logining()
    return render_template("login.html", message=message, user=user)


@app.route('/logout')
def logout():
    session['email'] = 'no_user'
    session['admin'] = False
    if 'no_user' not in session:
        session['no_user'] = {'favorites': [], 'shopping_cart': {}}
        session_modified()
    return redirect(url_for("index"))


@app.route('/add_to_sh_cart/<int:product_id>', methods=['GET', 'POST'])
def add_to_shopping_cart(product_id):
    return add(str(product_id), 'shopping_cart')


@app.route('/delete_sh_cart/<int:product_id>', methods=['GET', 'POST'])
def delete_from_shopping_cart(product_id):
    return delete(str(product_id), 'shopping_cart')


@app.route('/shopping_cart', methods=['GET', 'POST'])
def shopping_cart():
    message = False
    if session[session['email']]['shopping_cart']:
        products = db.select(f"SELECT * FROM product WHERE id IN {prods_shopping_cart()}")
        total_price = db.select(f"SELECT sum(price) FROM product WHERE id IN {prods_shopping_cart()}")
        session[session['email']]['total_price'] = total_price['sum']
        if isinstance(products, dict):
            products = [products]
    else:
        session[session['email']]['total_price'] = []
        total_price = session[session['email']]['total_price']
        products = None
        message = 'Корзина пуста'
    session_modified()
    user = user_logining()
    if products:
        quantity = [1] * len(products)
        products = zip(products, quantity)
    else:
        products = None
    context = {
        'title': 'Корзина',
        'products': products,
        'message': message,
        'user': user,
        'total_price': total_price,
        'exist': exist(),
        'site': 'shopping_cart'
    }

    return render_template("shopping_cart.html", **context)


@app.route('/add_to_favorites/<int:product_id>', methods=['GET', 'POST'])
def add_to_favorites(product_id):
    return add(product_id, 'favorites')


@app.route('/delete_favorites/<int:product_id>', methods=['GET', 'POST'])
def delete_from_favorites(product_id):
    return delete(product_id, 'favorites')


@app.route('/favorites', methods=['GET', 'POST'])
def favorites():
    message = False
    if session[session['email']]['favorites']:
        products = db.select(f"SELECT * FROM product WHERE id IN {prods_favorites()}")
        if isinstance(products, dict):
            products = [products]
    else:
        products = None
        message = 'В избранном ничего нет'
    user = user_logining()
    if products:
        quantity = [1] * len(products)
        products = zip(products, quantity)
    else:
        products = None
    context = {
        'title': 'Избранное',
        'products': products,
        'message': message,
        'user': user,
        'site': 'favorites',
        'exist': exist()
    }

    return render_template("favorites.html", **context)


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    message = None
    if prods_shopping_cart() != '()':
        products = db.select(f"SELECT * FROM product WHERE id IN {prods_shopping_cart()}")
    else:
        products = None
    print(session)
    if isinstance(products, dict):
        products = [products]
    if request.method == 'POST':
        order = request.form.get('order_products')
        user_email = db.select(f"SELECT id FROM mail_user WHERE email='{session['email']}'")['id']
        order_data = datetime.datetime.now()
        total_price = session[session['email']]['total_price']
        if order:
            products = list(map(int, session[session['email']]['shopping_cart'].keys()))
            db.insert(
                f"INSERT INTO user_order (mail_user, order_data, order_time, total_price, product, quantity) VALUES ('{user_email}', '{order_data}', '{order_data}', '{total_price}', '{products}', 111)")
            products = db.select(f"SELECT * FROM product WHERE id IN {prods_shopping_cart()}")
            if isinstance(products, dict):
                products = [products]
            session[session['email']].pop('total_price', None)
            session[session['email']]['shopping_cart'] = {}
            session_modified()
            message = 'Заказ успешно оформлен'
        else:
            message = 'Произошла ошибка'
    orders_exist = 1
    if products:
        quantity = [1] * len(products)
        products = zip(products, quantity)
    else:
        products = None
    return render_template("checkout.html", message=message, products=products, exist=exist(),
                           orders_exist=orders_exist)


@app.route('/orders')
def orders():
    user_in = db.select(f"SELECT id FROM mail_user WHERE email='{session['email']}'")['id']
    products_list = db.select(f"SELECT order_data, order_time, product FROM user_order WHERE mail_user='{user_in}'")
    message = None
    if products_list:
        products = []
        order_datas = []
        if isinstance(products_list, dict):
            products_list = [products_list]
        for product_order in products_list:
            order_data = product_order['order_data']
            order_time = product_order['order_time']
            order_datas.append(str(order_data) + ' ' + str(order_time).split('.')[0][:-3])
            product_order = product_order['product'][1:-1].split(',')
            products_from_bd = []
            for product in product_order:
                product = product
                prods = db.select(f"SELECT * FROM product WHERE id='{product}'")
                products_from_bd.append(prods)
            products.append(products_from_bd)
    else:
        message = 'Вы еще ничего не заказали'
        products = [None]
        order_datas = [None]
    user = user_logining()
    return render_template('orders.html', message=message, products=zip(products, order_datas), user=user)


@app.route('/profile')
def profile():
    user = user_logining()
    user_mail = db.select(f"SELECT * FROM mail_user WHERE email = '{session['email']}'")
    return render_template('profile.html', user_mail=user_mail, user=user)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    message = None
    user_data = db.select(f"SELECT * FROM mail_user WHERE email='{session['email']}'")
    if user_data['gender'] == 'Женский':
        gender = 1
    else:
        gender = 0
    if request.method == 'POST':
        email_edit = request.form.get('email')
        gender_edit = request.form.get('gender')
        name_edit = request.form.get('name')
        if email_edit != session['email'] and db.select(f"SELECT * FROM mail_user WHERE email = '{email_edit}'"):
            message = 'Данные нельзя поменять'
        elif user_data['email'] == email_edit and user_data['name'] == name_edit and request.form.get(
                'password') == '' and user_data['gender'] == gender_edit:
            message = 'Данные не были изменены'
        else:
            password_edit = generate_password_hash(request.form.get('password'))
            if request.form.get('password') != '':
                db.update(
                    f"UPDATE mail_user SET name='{request.form.get('name')}', gender = '{gender_edit}', email='{email_edit}', password='{password_edit}' WHERE mail_user.email = '{session['email']}'")
            else:
                db.update(
                    f"UPDATE mail_user SET name='{request.form.get('name')}', gender = '{gender_edit}', email='{email_edit}' WHERE mail_user.email = '{session['email']}'")
            if email_edit != session['email']:
                email_before_edit = session['email']
                session['email'] = email_edit
                session[session['email']] = session[email_before_edit]
                session.pop(email_before_edit, None)
                session_modified()
            message = 'Данные изменены'
            return redirect(url_for('profile', message=message))
    user = bool(user_logining())
    user_data = db.select(f"SELECT * FROM mail_user WHERE email='{session['email']}'")
    return render_template("edit_profile.html", user_data=user_data, user=user, message=message, gender=gender)


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    message = None
    if request.method == 'POST':
        db.insert(
            f"INSERT INTO product (name, short_description, description, price, category, image, brand, country, weight, composition, quantity) "
            f"VALUES ('{request.form.get('name')}', '{request.form.get('short_description')}', '{request.form.get('description')}', {float(request.form.get('price'))}, {int(request.form.get('category'))}, '{request.form.get('image')}', {int(request.form.get('brand'))}, {int(request.form.get('country'))}, {float(request.form.get('weight'))}, '{request.form.get('composition')}', {int(request.form.get('quantity'))})")
        message = 'Товар добавлен'
    user = user_logining()
    return render_template("add_product.html", message=message, user=user)


@app.route('/edit_product, <int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    message = None
    product = db.select(f"SELECT * FROM product WHERE id={product_id}")
    brand = is_in_db(request.form.get('brand'), 'brand', product)
    country = is_in_db(request.form.get('country'), 'country', product)
    category = is_in_db(request.form.get('category'), 'category', product)
    if request.method == 'POST':
        db.update(
            f"UPDATE product SET name='{request.form.get('name')}', short_description='{request.form.get('short_description')}', description='{request.form.get('description')}', price={float(request.form.get('price'))}, category={int(category)}, image='{request.form.get('image')}', brand={int(brand)}, country={int(country)}, weight={float(request.form.get('weight'))}, composition='{request.form.get('composition')}', quantity={int(request.form.get('quantity'))}")
        message = 'Данные изменены'
        return redirect(url_for('get_product', message=message, product_id=product_id))
    user = user_logining()
    product_data = db.select(f"SELECT * FROM product WHERE id={product_id}")
    print(product_data)
    return render_template("edit_product.html", message=message, user=user, product=product, admin=session['admin'], product_data=product_data)


@app.route('/delete_product, <int:product_id>', methods=['GET', 'POST'])
def delete_product(product_id):
    pass
if __name__ == '__main__':
    app.run(port=9000, debug=True, host='localhost')
