from datetime import date, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user 
import yfinance as yf
from flask import request,  render_template, jsonify, Flask
from sklearn.linear_model import LinearRegression
import numpy as np

auth = Blueprint('auth',__name__)

@auth.route('/')
def welcome():
    return render_template("welcome.html")

@auth.route('/member')
def member():
    return render_template("member.html")

@auth.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return render_template("home.html", user = current_user)
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
    if current_user.is_authenticated:
        return render_template("home.html", user = current_user)
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
    ##
    stock_ticker = yf.Ticker(symbol)
    name = stock_ticker.info['longName']      
    ##
    df = get_stock_price_thrend(symbol)
    data = df.values.tolist()
    for i in range(0,len(data)):
        data[i] = round(data[i],2)
    index = df.index.tolist()
    #
    future = predict_next_value(data,5)
    data.append(future[0])
    data.append(future[1])
    data.append(future[2])
    data.append(future[3])
    data.append(future[4])
    #
    for i in range(0,len(index)):
        index[i] = str(index[i])[6:10]
    #
    #print(index)
    index.append("Day1")
    index.append("Day2")
    index.append("Day3")
    index.append("Day4")
    index.append("Day5")
    return render_template("stock.html", user = current_user, stock = stock, name = name, price=data, date = index)

##
TODAY = date.today().strftime("%Y-%m-%d")
START = (date.today() - timedelta(days=56)).strftime("%Y-%m-%d")
def get_stock_price_thrend(stock):
    df = yf.download(stock, start=START, end=TODAY)["Close"]
    return df
##

def predict_next_value(values, num):
    #linear regression, accepting a list of N numbers.
    #:return: Predicted next (N+1) value.
    num_values = len(values)
    if num_values < 2:
        raise ValueError("At least 2 numbers")
    X = np.arange(num_values).reshape(-1, 1)  
    y = np.array(values)
    model = LinearRegression()
    model.fit(X, y)
    # Predict
    indices = np.arange(num_values, num_values + num).reshape(-1, 1)
    next_value = model.predict(indices)
    #print(next_value)
    return next_value.tolist()
#predict_next_value = predict_next_value(example)