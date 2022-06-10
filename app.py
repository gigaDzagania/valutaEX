from flask import Flask, redirect, url_for, render_template, request, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import generate_password_hash, check_password_hash
import requests
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'python'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite'
app.config['SQLALCHEMY_BINDS'] = {'valuta': 'sqlite:///valuta.sqlite'}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    lastname = db.Column(db.String(20), nullable=False)
    mail = db.Column(db.String(40), nullable=False)
    password = db.Column(db.String(80), nullable=False)


class Valuta(db.Model):
    __bind_key__ = 'valuta'
    id = db.Column(db.Integer, primary_key=True)
    val = db.Column(db.String(4), nullable=False)


@app.route('/home')
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        mail = request.form['mail']
        password = request.form['password']
        users = Users.query.filter_by(mail=mail).first()
        if not users or check_password_hash(users.password, password):
            flash("Username or password is incorrect !!!")
        else:
            session['mail'] = mail
            return redirect(url_for('convert'))
    return render_template('login.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        n = request.form['name']
        l = request.form['lastname']
        m = request.form['mail']
        p = request.form['password']
        p1 = request.form['password1']
        if n == '' or l == '' or m == '' or p == '':
            flash('Fill in all the required fields !', 'error')
        elif Users.query.filter_by(mail=m).first():
            flash('A similar E-mail has already been registered !', 'error')
        elif len(p) < 8:
            flash('The password must be at least 8 characters long !', 'error')
        elif p != p1:
            flash('Repeat the password correctly !', 'error')
        else:
            b1 = Users(name=n, lastname=l, mail=m, password=generate_password_hash(m))
            db.session.add(b1)
            db.session.commit()
            flash("Successful registration !", 'info')
    return render_template('register.html')


@app.route('/convert', methods=['GET', 'POST'])
def convert():

    lis = Valuta.query.all()
    name = Users.query.filter_by(mail=session['mail']).first().name

    try:
        if request.method == "POST":
            n = request.form['money']
            m = Valuta.query.filter_by(id=request.form['valuta1']).first().val
            p = Valuta.query.filter_by(id=request.form['valuta2']).first().val

            key = "XgSQJHRp4hi1emr1Lo6WeH4I6DSaynnJ"

            url = f"https://api.apilayer.com/currency_data/" \
                  f"convert?to={p}" \
                  f"&from={m}" \
                  f"&amount={n}" \
                  f"&apikey={key}"

            response = requests.get(url)

            with open('currency.json', 'w') as file:
                json.dump(json.loads(response.text), file, indent=4)

            dic_jso = response.json()

            res1 = (f"1 {dic_jso['query']['from']} "
                    f"= {round(dic_jso['info']['quote'], 2)} {dic_jso['query']['to']}")

            res2 = (f"{dic_jso['query']['amount']} {dic_jso['query']['from']} "
                    f"= {round(dic_jso['result'], 1)} {dic_jso['query']['to']}")

            return render_template('convert.html', res1=res1, res2=res2, lis=lis, name=name)
        else:
            return render_template('convert.html', lis=lis, name=name)

    except: return render_template('convert.html', lis=lis, name=name)


@app.route('/logout')
def logout():
    session.pop('mail', None)
    return redirect('/')


@app.errorhandler(404)
def invalid_route(e):
    return render_template('404.html')


if __name__ == "__main__":
    app.run(debug=True)
