import os

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import jsonify

from flask_cors import CORS

from flask_sqlalchemy import SQLAlchemy

import telnetlib
import socket

project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "statsmanager.db"))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app)

db = SQLAlchemy(app)

try:
    tn = telnetlib.Telnet('192.168.1.203', 5250, 10)
except OSError as e:
    print(e)


class Competitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(80), nullable=False)
    record = db.Column(db.Float, default=0)
    weight = db.Column(db.Float, default=0)
    weightclass_id = db.Column(db.Integer, db.ForeignKey('weight_class.id'), nullable=True)
    weightclass = db.relationship("WeightClass")
    order = db.Column(db.Integer, default=0)
    attempt1_weight = db.Column(db.Float, default=0)
    attempt1_result = db.Column(db.Integer, nullable=True, default=2)       # 0 = fail, 1 = pass, 2 = no attempt

    attempt2_weight = db.Column(db.Float, default=0)
    attempt2_result = db.Column(db.Integer, nullable=True, default=2)
    
    attempt3_weight = db.Column(db.Float, default=0)
    attempt3_result = db.Column(db.Integer, nullable=True, default=2)
    
    attempt4_weight = db.Column(db.Float, default=0)
    attempt4_result = db.Column(db.Integer, nullable=True, default=2)


class WeightClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    record = db.Column(db.Float)
    group = db.Column(db.Integer)
    order = db.Column(db.Integer)


# Current attempt
class Current(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    competitor_id = db.Column(db.Integer, db.ForeignKey('competitor.id'))
    competitor = db.relationship(Competitor)


def get_or_default(dict, key, default):
    try:
        return dict[key]
    except KeyError as e:
        return default


@app.route("/competitors/update", methods=["POST"])
def update():
    try:
        data = request.json
        competitor = Competitor.query.get(data['id'])
        competitor.name = get_or_default(data, 'newname', "Unnamed competitor")
        competitor.record = get_or_default(data, 'record', 0)
        competitor.weight = get_or_default(data, 'weight', 0)
        competitor.order = get_or_default(data, 'order', 0)
        competitor.attempt1_weight = get_or_default(data, 'attempt1_weight', 0)
        competitor.attempt1_result = get_or_default(data, 'attempt1_result', 2)

        competitor.attempt2_weight = get_or_default(data, 'attempt2_weight', 0)
        competitor.attempt2_result = get_or_default(data, 'attempt2_result', 2)

        competitor.attempt3_weight = get_or_default(data, 'attempt3_weight', 0)
        competitor.attempt3_result = get_or_default(data, 'attempt3_result', 2)

        competitor.attempt4_weight = get_or_default(data, 'attempt4_weight', 0)
        competitor.attempt4_result = get_or_default(data, 'attempt4_result', 2)

        db.session.commit()
    except Exception as e:
        print('Could not update competitor', e)
    return redirect("/#current")


@app.route("/delete", methods=["POST"])
def delete():
    id = request.form.get("id")
    competitor = Competitor.query.get(id)
    db.session.delete(competitor)
    db.session.commit()
    return redirect("/")


@app.route("/lowerthird/play", methods=["POST"])
def lowerthird_play():
    try:
        tn.write('CG 1-12 ADD 1 "chinup/LOWER-THIRD" 1'.encode('utf8') + b"\r\n")
    except NameError as e:
        print('Connection timed out')
        return redirect("/?error=1")
    else:
        return redirect("/")


@app.route("/lowerthird/stop", methods=["POST"])
def lowerthird_stop():
    try:
        tn.write('CG 1-12 STOP 1'.encode('utf8') + b"\r\n")
    except NameError as e:
        print('Connection timed out')
        return redirect("/?error=1")
    else:
        return redirect("/")

# Show current competitor /current/show ?? is get ok?
# Hide current competitor /current/hide ?? is get ok?
# Set current competitor POST /current
# Get current (for template) GET /current
# Get standings /weightclass/<id>/score
# Get competitor list in correct order /competition

# update Competitor (weight, record, attempt1-4)


@app.route("/competitors/next", methods=["POST"])
def next():
    if request.form:
        current = Current.query.first()
        next = Competitor.query.filter_by(order=current.competitor.order+1).first()
        try:
            current.competitor_id = next.id
            db.session.commit()
        except AttributeError as e:
            print('already at the end of the list', e)
        finally:
            return redirect("/#current")



@app.route("/competitors/current", methods=["GET", "POST"])
def current():
    if request.form:
        try:
            current = Current.query.first()
            current.competitor_id = request.form.get("id")
            db.session.commit()
        except AttributeError as e:
            current = Current(competitor_id=request.form.get("id"))
            db.session.add(current)
            db.session.commit()
        finally:
            return redirect("/#current")

    current = Current.query.first()
    return jsonify(name=current.competitor.name,
                   weight=current.competitor.weight,
                   record=current.competitor.record,
                   attempt1_weight=current.competitor.attempt1_weight,
                   attempt1_result=current.competitor.attempt1_result,
                   attempt2_weight=current.competitor.attempt2_weight,
                   attempt2_result=current.competitor.attempt2_result,
                   attempt3_weight=current.competitor.attempt3_weight,
                   attempt3_result=current.competitor.attempt3_result,
                   attempt4_weight=current.competitor.attempt4_weight,
                   attempt4_result=current.competitor.attempt4_result,
    )

@app.route("/competitors", methods=["POST"])
def competitors():
    if request.form:
        try:
            competitor = Competitor(name=request.form.get("name"))
            db.session.add(competitor)
            db.session.commit()
        except Exception as e:
            print('Failed to add competitor')

        current = Current.query.first()
        if current is None:
            current = Current(competitor_id=competitor.id)
            db.session.add(current)
            db.session.commit()

    return redirect("/")


@app.route("/", methods=["GET"])
def home():
    competitors = None

    competitors = Competitor.query.order_by(Competitor.order).all()
    current = Current.query.first()

    return render_template("home.html", competitors=competitors, current=current)

if __name__ == "__main__":
    app.run(debug=True)
