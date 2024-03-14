from datetime import date, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user 

#
import yfinance as yf
from flask import request,  render_template, jsonify, Flask
#

auth = Blueprint('auth',__name__)

@auth.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password', category='error')
        else:
            flash('email doesn\'t exit.', category='error')

    return render_template("login.html", user = current_user)


@auth.route('/logout')
#@login_required
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('Logout succeed!', category='success')
        return redirect(url_for('auth.login'))
    else:
        flash('You have already logged out!', category='error')
        return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET','POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exits', category='error')
        elif password1 != password2:
            flash('Your passwords don\'t match!', category='error')
        elif len(password1) < 8:
            flash('Password must be at least 8 characters', category='error')
        else: #add user to the database
            new_user = User(email=email,password = generate_password_hash(password1, method='pbkdf2'))
            db.session.add(new_user)
            db.session.commit()
            flash('Account created!', category='success')
            user = User.query.filter_by(email=email).first()
            login_user(user, remember=True)
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user = current_user)

@auth.route('/stock/<symbol>')
def stock_detail(symbol):
    for note in current_user.notes:
        if note.data == symbol:
            stock = note
    df = get_stock_price_thrend(symbol)
    data = df.values.tolist()
    for i in range(0,len(data)):
        data[i] = round(data[i],2)
    index = df.index.tolist()
    
    #
    for i in range(0,len(index)):
        index[i] = str(index[i])[0:10]
    #

    return render_template("stock.html", user = current_user, stock = stock, data=data, date = index)

### get the real time stock price
@auth.route('/get_stock_data',methods=['POST'])
def get_stock_data():
    ticker = request.get_json()['ticker']
    data = yf.Ticker(ticker).history(period='1y')
    return jsonify({'currentPrice': data.iloc[-1].Close, 'openPrice': data.iloc[-1].Open})
##

TODAY = date.today().strftime("%Y-%m-%d")
START = date.today() - timedelta(days=56)

START = START.strftime("%Y-%m-%d")
def get_stock_price_thrend(stock):
    df = yf.download(stock, start=START, end=TODAY)["Close"]
    return df