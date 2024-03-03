from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user 
from . import db
from .models import Note
from . import db
import json

views = Blueprint('views',__name__)

@views.route('/', methods=['GET','POST'])
@login_required
def home():
    if request.method == 'POST':
        note =request.form.get('note')
        if note[0] == ' ':
            note = note[1:]
        flag = True
        for char in note:
            if char.isalpha() and not char.isupper():
                flag = False
            if not char.isalpha():
                flag = False
        if len(note) < 1 or len(note) > 4 or not flag:
            flash('Stock Code Error! Stock code should not be longer than 4 characters or less than 1 character', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id, price=0.00)
            db.session.add(new_note)
            db.session.commit()
            flash('Stock added!', category='success')

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