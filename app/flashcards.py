from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import random
import os

app = Flask(__name__)
app.secret_key = os.environ["FSK"]
target_path = os.path.abspath(__file__) + "/../instance/flashcards.db"
print("path: ", target_path)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{target_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

if not os.path.exists(target_path):
    with app.app_context():
        db.create_all()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    decks = db.relationship("Deck", backref="user", lazy=True)

class Deck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    cards = db.relationship("Card", backref="deck", lazy=True)

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    deck_id = db.Column(db.Integer, db.ForeignKey("deck.id"), nullable=False)

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/login', methods=["POST"])
def login():
    username = request.form["Username"].strip()
    user = User.query.filter_by(name=username).first()
    if not user:
        return jsonify({
            "result": "False"
        })

    session["user_id"] = user.id
    return jsonify({
        "result" : "True"
    })

@app.route("/fresh_start")
def fresh_start():
    return render_template("new_user.html")

@app.route("/create_user", methods=["POST"])
def create_user():
    username = request.form["Username"].strip()
    existing_user = User.query.filter_by(name=username).first()
    if existing_user:
        return jsonify({
            "result" : "False"
        })
    else:
        new_user = User(name=username)
        db.session.add(new_user)
        db.session.commit()
        session["user_id"] = new_user.id
        return jsonify({
            "result" : "True"
        })

@app.route("/dashboard")
def dashboard():
    print("Logging in with User ID", session["user_id"])
    user = User.query.get(session["user_id"])
    return render_template("dashboard.html", decks=user.decks, user=user)

@app.route("/create_deck", methods=["POST"])    
def create_deck():
    
    deck_name = request.form["deck_name"]
    user_id = session["user_id"]

    new_deck = Deck(name=deck_name, user_id=user_id)
    db.session.add(new_deck)
    db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/rename_deck/<int:deck_id>/<newname>")
def rename_deck(deck_id, newname):
    deck = Deck.query.get_or_404(deck_id)
    deck.name = newname
    db.session.commit()
    return jsonify({})

@app.route("/delete_deck/<int:deck_id>")
def delete_deck(deck_id):
    Deck.query.filter(Deck.id == deck_id).delete(synchronize_session=False)
    Card.query.filter(Card.deck_id == deck_id).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({})

@app.route("/deck/<int:deck_id>")
def view_deck(deck_id):
    deck = Deck.query.get(deck_id)
    if not deck:
        return redirect(url_for("index"))
    
    correct_user = User.query.get(deck.user_id)
    if session["user_id"] != correct_user.id:
        print(f"ID mismatch between session ID {session['user_id']} and true ID {correct_user.id}")
        return redirect(url_for("index"))
    
    print("Viewing Deck with ID", deck_id)
    deck = Deck.query.get_or_404(deck_id)
    cards = Card.query.filter_by(deck_id=deck_id).all()
    return render_template("deck.html", deck=deck, cards=cards)

@app.route("/deck/<int:deck_id>/add_card", methods=["POST"])
def add_card(deck_id):
    question = request.form["new_question"]
    answer = request.form["new_answer"]
    new_card = Card(question=question, answer=answer, deck_id=deck_id)
    db.session.add(new_card)
    db.session.commit()
    return redirect(url_for("view_deck", deck_id=deck_id))

@app.route("/edit_card/<int:card_id>", methods=["POST"])
def edit_card(card_id):
    print(f"Card with ID {card_id} edited")
    card = Card.query.get_or_404(card_id)
    data = request.json
    card.question = data.get("question", card.question)
    card.answer = data.get("answer", card.answer)
    db.session.commit()
    return jsonify({})

@app.route("/get_card/<int:card_id>")
def get_card(card_id):
    print("Card opened with ID", card_id)
    card = Card.query.get_or_404(card_id)
    return jsonify({
        "question": card.question, 
        "answer": card.answer
    })

@app.route("/delete_card/<int:deck_id>/<int:card_id>")
def delete_card(deck_id, card_id):
    Card.query.filter(Card.id == card_id).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({})

@app.route("/quiz/<int:deck_id>")
def quiz(deck_id):
    deck = Deck.query.get(deck_id)
    if not deck:
        return redirect(url_for("index"))
        
    correct_user = User.query.get(deck.user_id)
    if session["user_id"] != correct_user.id:
        print(f"ID mismatch between session ID {session['user_id']} and true ID {correct_user.id}")
        return redirect(url_for("index"))
    
    print(f"Quiz started with Deck ID {deck_id}")
    cards = Card.query.filter_by(deck_id=deck_id).all()
    cards_length = len(cards)
    if cards_length >= 5:
        selection = random.sample(cards, k=5)
    else:
        selection = random.sample(cards, cards_length)
    
    selection_data = []
    for card in selection:
        current = {
            "id" : card.id,
            "question" : card.question,
            "answer" : card.answer,
            "deck_id" : card.deck_id
        }
        selection_data.append(current)


    return render_template("quiz.html", cards=selection_data, deck_id=deck_id)

if __name__ == "__main__":
    app.run(debug=True)