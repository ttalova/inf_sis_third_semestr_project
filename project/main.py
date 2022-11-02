from flask import Flask, redirect, url_for, render_template, request, make_response, session
from flask_login import LoginManager
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

    # получаем GET-параметр country (Russia/USA/French
    name = request.args.get("name")
    description = request.args.get("description")
    price = request.args.get("price")
    category = request.args.get("category")
    image = request.args.get("image")
    brand = request.args.get("brand")
    country = request.args.get("country")

    # if rating:
    #     films = [x for x in films if float(x['rating']) >= float(rating)]
    # # формируем контекст, который мы будем передавать для генерации шаблона
    context = {
        'products': products,
        'title': "Products",
        'name': name,
        'description': description,
        'price': price,
        'category': category,
        'image': image,
        'brand': brand,
        'country': country
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
    is_seccess = False
    message = None
    if request.method == "POST":
        user = db.select(f"SELECT * FROM mail_user WHERE mail_user.email = '{request.form.get('email')}'")
        if user and user['password'] == request.form.get('password'):
            is_seccess = True
            return redirect(url_for('index'))
        else:
            message = 'Неправильный логин или пароль'
    return render_template("login.html", message=message, is_seccess=is_seccess)

@app.route('/profile')
def profile():
    return render_template('profile.html')


if __name__ == '__main__':
    app.run(port=9000, debug=True, host='localhost')
