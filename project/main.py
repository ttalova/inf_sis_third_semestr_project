import random

from flask import Flask, redirect, url_for, render_template, request, make_response, session

import datetime

from db_util import Database

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import os

from help_functions import *

import random
from secret import secret_key


def page_not_found(e):
    return render_template("error.html")


UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__, static_folder='./static')
app.secret_key = secret_key
app.permanent_session_lifetime = datetime.timedelta(days=365)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.register_error_handler(404, page_not_found)
db = Database()


@app.route('/products', methods=['GET', 'POST'])
def index():
    session.setdefault('admin', False)
    if 'email' not in session:
        session['email'] = 'no_user'
        session[session['email']] = {'favorites': [], 'shopping_cart': {}}
    session_modified()
    products = db.select(f"SELECT * FROM product")
    day_product = random.choice(products)
    categories = db.select(f"SELECT * FROM category")
    search = ''
    products = isinstance_dict(products)
    categories = isinstance_dict(categories)
    if request.method == 'POST':
        search = request.form.get('search', '')
        category = request.form.get('category')
        if search:
            products = [product for product in products if
                        search.lower() in product['name'].lower() or search.lower() in product['description'].lower()]
        if category == None:
            category = 0
        if int(category):
            products = [product for product in products if
                        int(category) == product['category']]
    products = prepare_data_of_products(products)
    context = {
        'products': products,
        'title': "Products",
        'exist': exist(),
        'user': user_logining(),
        'search': search,
        'categories': categories,
        'site': 'index',
        'admin': session['admin'],
        'category_selected': int(request.form.get('category')) if request.form.get('category') else '',
        'indexx': 1,
        'day_product': day_product
    }
    return render_template("index.html", **context)


@app.route("/products/<int:product_id>")
def get_product(product_id):
    product = db.select(f"SELECT * FROM product WHERE id = {product_id}")
    if type(product) != int:
        content = {
            'title': product['name'],
            'product': product,
            'category': db.select(f"SELECT name FROM category WHERE id='{product['category']}'"),
            'country': db.select(f"SELECT name FROM country WHERE id='{product['country']}'"),
            'brand': db.select(f"SELECT name FROM brand WHERE id='{product['brand']}'"),
            'admin': session['admin'],
            'exist': exist(),
            'site': 'get_product'
        }
        return render_template("product.html", **content)
    return render_template("error.html", error="Такого товара не существует")


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    message = None
    if request.method == 'POST':
        user = db.select(f"SELECT * FROM mail_user WHERE mail_user.email = '{request.form.get('email')}'")
        if not user:
            password = generate_password_hash(request.form.get('password'))
            db.insert(
                f"INSERT INTO mail_user (name, gender, email, password, role) VALUES ('{request.form.get('name')}',"
                f" '{request.form.get('gender')}', '{request.form.get('email')}', '{password}', 'user')")
            session['email'] = request.form.get('email')
            session[session['email']] = {'favorites': [], 'shopping_cart': {}}
            sum_favorites(session['email'])
            session['admin'] = False
            session_modified()
            return redirect(url_for("index"))
        else:
            message = 'Исправьте ошибки'
    content = {
        'message': message,
        'user': user_logining(),
        'user_data': [{'name': '', 'email': '', 'gender': '', 'password': ''}],
        'title': 'Регистрация'
    }
    return render_template("signup.html", **content)


@app.route("/login", methods=["POST", "GET"])
def login():
    message = None
    if request.method == "POST":
        user = db.select(f"SELECT * FROM mail_user WHERE mail_user.email = '{request.form.get('email')}'")
        if user and check_password_hash(user['password'], request.form.get('password')):
            session['email'] = request.form.get('email')
            if user['role'] == 'admin':
                session['admin'] = True
            if session['email'] not in session:
                session[session['email']] = {'favorites': [], 'shopping_cart': {}}
            sum_favorites(session['email'])
            session_modified()
            return redirect(url_for("index"))
        else:
            message = 'Неправильный логин или пароль'
    return render_template("login.html", message=message, user=user_logining(), title='Вход')


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
        products = db.select(f"SELECT * FROM product WHERE id IN {prods_shopping_cart()} AND status='in'")
        total_price = db.select(f"SELECT sum(price) FROM product WHERE id IN {prods_shopping_cart()} AND status='in'")
        session[session['email']]['total_price'] = total_price['sum']
        products = isinstance_dict(products)
    else:
        session[session['email']]['total_price'] = []
        total_price = session[session['email']]['total_price']
        session_modified()
        products = None
        message = 'В корзине ничего нет...'
    if products == 0:
        products = None
        message = 'В корзине ничего нет...'
        session[session['email']]['shopping_cart'] = {}
        session[session['email']]['total_price'] = []
        total_price = session[session['email']]['total_price']
    session_modified()
    context = {
        'title': 'Корзина',
        'products': prepare_data_of_products(products),
        'message': message,
        'user': user_logining(),
        'total_price': total_price,
        'exist': exist(),
        'site': 'shopping_cart',
        'admin': session['admin']
    }
    # if request.method == 'POST' and not user_logining():
    #     return redirect(url_for('checkout', **context))
    # else:
    #     return redirect(url_for('signup'))

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
        products = db.select(f"SELECT * FROM product WHERE id IN {prods_favorites()} AND status='in'")
        products = isinstance_dict(products)
    else:
        products = None
        message = 'В избранном ничего нет...'
    if products == 0:
        products = None
        message = 'В избранном ничего нет...'
        session[session['email']]['favorites'] = []
        session_modified()
    context = {
        'title': 'Избранное',
        'products': prepare_data_of_products(products),
        'message': message,
        'user': user_logining(),
        'site': 'favorites',
        'exist': exist(),
        'admin': session['admin']
    }
    return render_template("favorites.html", **context)


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    message = None
    if prods_shopping_cart() != '()':
        products = db.select(f"SELECT * FROM product WHERE id IN {prods_shopping_cart()} AND status='in'")
    else:
        products = None
    products = isinstance_dict(products)
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        second_name = request.form.get('second_name')
        third_name = request.form.get('third_name')
        adress = request.form.get('address')
        city = request.form.get('city')
        order = request.form.get('order_products')
        user_email = db.select(f"SELECT id FROM mail_user WHERE email='{session['email']}'")['id']
        order_data = datetime.datetime.now()
        total_price = session[session['email']]['total_price']
        if order:
            products = db.select(f"SELECT id FROM product WHERE id IN {prods_shopping_cart()} AND status='in'")
            print(products)
            products = isinstance_dict(products)
            products = [id['id'] for id in products]
            num_order = generate_password_hash(str(products) + str(random.randint(1, 100)))
            for product in products:
                db.insert(
                    f"INSERT INTO user_order (mail_user, order_data, order_time, total_price, product, first_name, second_name, third_name, city, adress, num_order) VALUES ('{user_email}', '{order_data}', '{order_data}', '{total_price}', '{product}', '{first_name}', '{second_name}', '{third_name}', '{city}', '{adress}', '{num_order}')")
            products = db.select(f"SELECT * FROM product WHERE id IN {prods_shopping_cart()}")
            products = isinstance_dict(products)
            db.update(f"UPDATE product SET quantity=quantity - 1 WHERE id IN {prods_shopping_cart()} AND status='in'")
            session[session['email']].pop('total_price', None)
            session[session['email']]['shopping_cart'] = {}
            session_modified()
            message = 'Заказ успешно оформлен'
        else:
            message = 'Произошла ошибка'
    context = {
        'message': message,
        'products': prepare_data_of_products(products),
        'exist': exist(),
        'orders_exist': 1,
        'admin': session['admin'],
        'user': user_logining()
    }
    return render_template("checkout.html", **context)


@app.route('/orders')
def orders():
    user_in = db.select(f"SELECT id FROM mail_user WHERE email='{session['email']}'")['id']
    orders_list = db.select(
        f"SELECT num_order, mail_user FROM user_order WHERE mail_user='{user_in}' ORDER BY order_data DESC, order_time DESC")
    if orders_list:
        orders_list = (isinstance_dict(orders_list))
        products = []
        orders_list = set([a['num_order'] for a in orders_list])
        order_datas = []
        total_prices = []
        for orderr in orders_list:
            products_list = db.select(
                f"SELECT * FROM user_order WHERE mail_user='{user_in}' AND num_order='{orderr}' ORDER BY order_data DESC, order_time DESC ")
            products_list = isinstance_dict(products_list)
            products_list_in = [a['product'] for a in products_list]
            middle = []
            for pr in products_list_in:
                middle.append(db.select(f"SELECT * FROM product WHERE id={pr}"))
            products.append(middle)
            order_data = products_list[0]['order_data']
            order_time = products_list[0]['order_time']
            total_price = products_list[0]['total_price']
            order_datas.append(str(order_data) + ' ' + str(order_time).split('.')[0][:-3])
            total_prices.append(str(total_price))
            message = None
    else:
        message = 'Вы еще ничего не заказали...'
        products = [None]
        order_datas = [None]
        total_prices = [None]
        orders_list = [None]
    context = {
        'message': message,
        'products': zip(orders_list, products, order_datas, total_prices),
        'user': user_logining(),
        'admin': session['admin']
    }
    return render_template('orders.html', **context)


@app.route('/profile')
def profile():
    user_mail = db.select(f"SELECT * FROM mail_user WHERE email = '{session['email']}'")
    context = {
        'user_mail': user_mail,
        'user': user_logining(),
        'admin': session['admin']
    }
    return render_template('profile.html', **context)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    message = None
    user_data = db.select(f"SELECT * FROM mail_user WHERE email='{session['email']}'")
    gender = 1 if user_data['gender'] == 'Женский' else 0
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
    user_data = db.select(f"SELECT * FROM mail_user WHERE email='{session['email']}'")
    context = {
        'user_data': user_data,
        'user': user_logining(),
        'message': message,
        'gender': gender,
        'admin': session['admin'],
        'title': 'Редактировать данные'
    }
    return render_template("signup.html", **context)


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    message = None
    if request.method == 'POST':
        file = request.files['photo']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        try:
            price = float(request.form.get('price').replace(' ', ''))
        except:
            price = -1
        if price <= 0:
            print(1)
            message = 'Некорректные данные'
        else:
            try:
                db.insert(
                    f"INSERT INTO product (name, short_description, description, price, category, image, brand, country, weight, composition, quantity, status) "
                    f"VALUES ('{request.form.get('name')}', '{request.form.get('short_description')}', '{request.form.get('description')}', {price}, {int(request.form.get('category'))}, '{filename}', {int(request.form.get('brand'))}, {int(request.form.get('country'))}, {float(request.form.get('weight').replace(' ', ''))}, '{request.form.get('composition')}', {int(request.form.get('quantity'))}, 'in')")
                message = 'Товар добавлен'
            except:
                message = 'Некорректные данные'

    context = {
        'admin': session['admin'],
        'message': message,
        'user': user_logining(),
        'category': get_list_of('category'),
        'country': get_list_of('country'),
        'brand': get_list_of('brand'),
    }
    return render_template("add_product.html", **context)


@app.route('/edit_product, <int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    message = None
    product = db.select(f"SELECT * FROM product WHERE id={product_id}")
    if request.method == 'POST':
        brand = is_in_db(request.form.get('brand'), 'brand', product)
        country = is_in_db(request.form.get('country'), 'country', product)
        category = is_in_db(request.form.get('category'), 'category', product)
        if 'file' in request.files:
            file = request.files['photo']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = 0
        try:
            price = float(request.form.get('price').replace(' ', ''))
        except:
            price = -1
        if price <= 0:
            message = 'Некорректные данные'
        else:
            if filename:
                db.update(
                    f"UPDATE product SET name='{request.form.get('name')}', short_description='{request.form.get('short_description')}',"
                    f" description='{request.form.get('description')}', price={price}, "
                    f"category={int(category)}, image='{filename}', brand={int(brand)}, country={int(country)}, "
                    f"weight={float(request.form.get('weight').replace(' ', ''))}, composition='{request.form.get('composition')}',"
                    f" quantity={int(request.form.get('quantity'))} WHERE id={product_id}")
            else:
                db.update(
                    f"UPDATE product SET name='{request.form.get('name')}', short_description='{request.form.get('short_description')}', "
                    f"description='{request.form.get('description')}', price={price}, "
                    f"category={int(category)}, brand={int(brand)}, country={int(country)}, weight={float(request.form.get('weight').replace(' ', ''))},"
                    f" composition='{request.form.get('composition')}', quantity={int(request.form.get('quantity'))} WHERE id={product_id}")
            message = 'Данные изменены'
        return redirect(url_for('get_product', message=message, product_id=product_id))
    context = {
        'message': message,
        'user': user_logining(),
        'product': product,
        'admin': session['admin'],
        'category': get_list_of('category'),
        'country': get_list_of('country'),
        'brand': get_list_of('brand')
    }
    return render_template("edit_product.html", **context)


@app.route('/delete_product, <int:product_id>', methods=['GET', 'POST'])
def delete_product(product_id):
    db.update(f"UPDATE product SET status='delete' WHERE id={product_id}")
    return redirect(url_for('index'))


@app.route('/cancel_delete_product, <int:product_id>', methods=['GET', 'POST'])
def cancel_delete_product(product_id):
    db.update(f"UPDATE product SET status='in' WHERE id={product_id}")
    return redirect(url_for('get_product', product_id=product_id))


if __name__ == '__main__':
    app.run(port=9000, debug=True, host='localhost')
