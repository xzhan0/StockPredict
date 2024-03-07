from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user 
from . import db
from .models import Note
from . import db
import random
import json
import yfinance as yf

views = Blueprint('views',__name__)

@views.route('/', methods=['GET','POST'])
@login_required
def home():
    if request.method == 'POST':
        note =request.form.get('note')
        try:
            stockCode = note
            stock = yf.Ticker(stockCode)
            note = note.upper()
            new_note = Note(data=note, user_id=current_user.id, price=getPrice(note))
            db.session.add(new_note)
            db.session.commit()
            flash('Stock added!', category='success')           
        except:
            flash('Stock Code Error! The stock code doesn\'t exists', category='error')

    return render_template("home.html", user=current_user)


@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId= note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
            flash('Stock removed!', category='success')
    return jsonify({})

@views.route('/refresh-stock', methods=['POST'])
def refresh_stock():
    user = current_user
    for note in user.notes:
        stockCode = note.data
        stock = yf.Ticker(stockCode)
        temp = stock.history()
        price = temp['Close'].iloc[-1]
        price = round(price, 2)
        note.price = price
        db.session.commit()
    return jsonify({})

def getPrice(code):
    stockCode = code
    stock = yf.Ticker(stockCode)
    temp = stock.history()
    price = temp['Close'].iloc[-1]
    price = round(price, 2)
    return price