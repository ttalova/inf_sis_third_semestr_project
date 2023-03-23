from main import db
from flask import Flask, redirect, url_for, render_template, request, session


def isinstance_dict(name):
    if isinstance(name, dict):
        name = [name]
    return name


def prepare_data_of_products(products):
    if products:
        quantity = [1] * len(products)
        products = zip(products, quantity)
    else:
        products = None
    return products


def user_logining():
    user = session['email']
    return user == 'no_user'


def sum_favorites(user):
    if len(session['no_user']) != 0:
        session[user]['favorites'] += session['no_user']['favorites']
        session[user]['shopping_cart'].update(session['no_user']['shopping_cart'])
        session.pop('no_user', None)
        session_modified()


def exist():
    return {'favorites': session[session['email']]['favorites'],
            'shopping_cart': list(map(int, session[session['email']]['shopping_cart'].keys()))}


def add(product_id, type_sqreen):
    if product_id not in session[session['email']][type_sqreen]:
        if type_sqreen == 'shopping_cart':
            session[session['email']][type_sqreen][product_id] = 1
        else:
            session[session['email']][type_sqreen].append(product_id)
    if not session.modified:
        session.modified = True
    user = user_logining()
    return redirect(url_for(request.args.get('site'), product_id=product_id, exist=exist(), user=user))


def delete(product_id, type_sqreen):
    if product_id in session[session['email']][type_sqreen]:
        if type_sqreen == 'shopping_cart':
            session[session['email']][type_sqreen].pop(product_id)
        else:
            session[session['email']][type_sqreen].remove(product_id)
    if not session.modified:
        session.modified = True
    user = user_logining()
    return redirect(url_for(request.args.get('site'), product_id=product_id, exist=exist(), user=user))


def prods_shopping_cart():
    return "(" + str(list(map(int, session[session['email']]['shopping_cart'].keys())))[1:-1] + ")"


def prods_favorites():
    return '(' + str(session[session['email']]['favorites'])[1:-1] + ')'


def session_modified():
    if not session.modified:
        session.modified = True


def is_in_db(get_data, parametr, db):
    if get_data == '0':
        return db[parametr]
    return get_data


def get_list_of(name_of_table):
    return db.select(f"SELECT id, name FROM {name_of_table}")


def page_not_found():
    return render_template("error.html")
