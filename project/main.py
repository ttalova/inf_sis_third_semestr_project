from flask import Flask, redirect, url_for, render_template, request, make_response, session
import datetime
from db_util import Database


app = Flask(__name__)
app.secret_key = '111'
# необходимо добавлять, чтобы время сессии не ограничивалось закрытием браузера
app.permanent_session_lifetime = datetime.timedelta(days=365)

# инициализация класса с методами для работы с БД
db = Database()

@app.route('/products', methods=['GET', 'POST'])
def index():
    products = db.select(f"SELECT * FROM product")
    id = request.args.get("id")
    name = request.args.get("name")
    description = request.args.get("description")
    price = request.args.get("price")
    category = request.args.get("category")
    image = request.args.get("image")
    brand = request.args.get("brand")
    country = request.args.get("country")
    if 'shopping_cart' not in session:
        exist = []
    else:
        exist = session['shopping_cart']

    if 'email' in session:
        user = session['email']
    else:
        user = None


    # if rating:
    #     films = [x for x in films if float(x['rating']) >= float(rating)]
    # # формируем контекст, который мы будем передавать для генерации шаблона
    context = {
        'products': products,
        'title': "Products",
        'id': id,
        'name': name,
        'description': description,
        'price': price,
        'category': category,
        'image': image,
        'brand': brand,
        'country': country,
        'exist': exist,
        'user': user
    }
    # возвращаем сгенерированный шаблон с нужным нам контекстом
    return render_template("index.html", **context)


@app.route("/products/<int:product_id>")
def get_product(product_id):
    # используем метод-обертку для выполнения запросов к БД
    product = db.select(f"SELECT * FROM product WHERE id = {product_id}")

    if len(product):
        return render_template("product.html", title=product['name'], product=product)

    # если нужный фильм не найден, возвращаем шаблон с ошибкой
    return render_template("error.html", error="Такого товара не существует")

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    message = None
    if request.method == 'POST':
        user = db.select(f"SELECT * FROM mail_user WHERE mail_user.email = '{request.form.get('email')}'")
        if not user:
            db.insert(
                    f"INSERT INTO mail_user (name, email, password) VALUES ('{request.form.get('name')}', '{request.form.get('email')}', '{request.form.get('password')}')")
            message = 'Вы успешно зарегистрированы'
        else:
            message = 'Исправьте ошибки'
    return render_template("signup.html", message=message)

@app.route("/login", methods=["POST", "GET"])
def login():
    message = None
    if request.method == "POST":
        user = db.select(f"SELECT * FROM mail_user WHERE mail_user.email = '{request.form.get('email')}'")
        if user and user['password'] == request.form.get('password'):
            session['email'] = request.form.get('email')  # чтение и обновление данных сессии
            return redirect(url_for("index", user=user))
        if not session.modified:
            session.modified = True
        else:
            message = 'Неправильный логин или пароль'
    return render_template("login.html", message=message)

@app.route('/profile')
def profile():
    user = user_logining()
    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for("index"))

@app.route('/add_to_sh_cart/<int:product_id>', methods=['GET', 'POST'])
def add_to_shopping_cart(product_id):
    exist = False
    if 'shopping_cart' in session:
        if product_id in session['shopping_cart']:
            exist = True
        else:
            session['shopping_cart'].append(product_id)
    else:
        session['shopping_cart'] = [product_id]
    if not session.modified:
        session.modified = True

    user = user_logining()
    return redirect(url_for("index", exist = exist, user = user))

@app.route('/delete_sh_cart/<int:product_id>', methods=['GET', 'POST'])
def delete_from_shopping_cart(product_id):
    exist = True
    if 'shopping_cart' in session:
        if product_id in session['shopping_cart']:
            exist = False
            session['shopping_cart'].remove(product_id)
    if len(session['shopping_cart']) == 0:
        session.pop('shopping_cart', None)
    if not session.modified:
        session.modified = True
    user = user_logining()
    return redirect(url_for("index", exist = exist, user=user))


@app.route('/shopping_cart', methods=['GET', 'POST'])
def shopping_cart():
    message = False
    if 'shopping_cart' in session:
        prods = '(' + str(session['shopping_cart'])[1:-1] + ')'
        products = db.select(f"SELECT * FROM product WHERE id IN {prods}")
        if type(products) == dict:
            products = [products]
    else:
        products = None
        message = 'Корзина пуста'
    user = user_logining()
    context = {
        'title': 'Корзина',
        'products': products,
        'message': message,
        'user': user
    }

    return render_template("shopping_cart.html", **context)

def user_logining():
    if 'email' in session:
        user = session['email']
    else:
        user = None
    return user
if __name__ == '__main__':
    app.run(port=9000, debug=True, host='localhost')
