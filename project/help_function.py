from flask import Flask, redirect, url_for, render_template, request, make_response, session
import datetime
from db_util import Database
from werkzeug.security import generate_password_hash, check_password_hash
def user_logining():
    user = session['email']
    return user == 'no_user'
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
    return redirect(url_for(request.args.get('site'), exist=exist(), user=user))

def delete(product_id, type_sqreen):
    if product_id in session[session['email']][type_sqreen]:
        if type_sqreen == 'shopping_cart':
            session[session['email']][type_sqreen].pop(product_id)
        else:
            session[session['email']][type_sqreen].remove(product_id)
    if not session.modified:
        session.modified = True
    user = user_logining()
    return redirect(url_for(request.args.get('site'), exist=exist(), user=user))

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
# def quantity_of_goods():
#     if request.form.get('quantity_order'):
#         print(request.form.get('quantity_order'))
#         for product in session[session['email']]['shopping_cart']:
#             session[session['email']]['shopping_cart'][product] = request.form.get('quantity_order')
#     session_modified()
#     print(111111, session)
#     return list(map(int, session[session['email']]['shopping_cart'].values()))
#
