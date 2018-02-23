import os

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import jsonify

from flask_cors import CORS

from flask_sqlalchemy import SQLAlchemy

project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "statsmanager.db"))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app)

db = SQLAlchemy(app)


class Competitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # add many to many
    name = db.Column(db.String(80), nullable=False)
    record = db.Column(db.Float)
    weight = db.Column(db.Float)
    weightclass_id = db.Column(db.Integer, db.ForeignKey('weight_class.id'), nullable=True)
    weightclass = db.relationship("WeightClass")
    order = db.Column(db.Integer)
    attempt1_weight = db.Column(db.Float)
    attempt1_result = db.Column(db.Boolean, nullable=True)

    attempt2_weight = db.Column(db.Float)
    attempt2_result = db.Column(db.Boolean, nullable=True)
    
    attempt3_weight = db.Column(db.Float)
    attempt3_result = db.Column(db.Boolean, nullable=True)
    
    attempt4_weight = db.Column(db.Float)
    attempt4_result = db.Column(db.Boolean, nullable=True)


class WeightClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    max_weight = db.Column(db.Float)
    record = db.Column(db.Float)
    group = db.Column(db.Integer)
    order = db.Column(db.Integer)


# Current attempt
class Current(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    competitor_id = db.Column(db.Integer, db.ForeignKey('competitor.id'))
    competitor = db.relationship(Competitor)


@app.route("/competitors/update", methods=["POST"])
def update():
    try:
        print(request.form.get("attempt1_result"))
        newname = request.form.get("newname")
        id = request.form.get("id")
        competitor = Competitor.query.get(id)
        competitor.name = newname
        competitor.record = request.form.get("record")
        competitor.weight = request.form.get("weight")
        competitor.order = request.form.get("order")
        competitor.attempt1_weight = request.form.get("attempt1_weight")
        competitor.attempt1_result = request.form.get("attempt1_result")
        competitor.attempt2_weight = request.form.get("attempt2_weight")
        competitor.attempt2_result = request.form.get("attempt2_result")
        competitor.attempt3_weight = request.form.get("attempt3_weight")
        competitor.attempt3_result = request.form.get("attempt3_result")
        competitor.attempt4_weight = request.form.get("attempt4_weight")
        competitor.attempt4_result = request.form.get("attempt4_result")
        db.session.commit()
    except Exception as e:
        print('Could not update competitor', e)
    return redirect("/")


@app.route("/delete", methods=["POST"])
def delete():
    id = request.form.get("id")
    competitor = Competitor.query.get(id)
    db.session.delete(competitor)
    db.session.commit()
    return redirect("/")

# Show current competitor /current/show ?? is get ok?
# Hide current competitor /current/hide ?? is get ok?
# Set current competitor POST /current
# Get current (for template) GET /current
# Get standings /weightclass/<id>/score
# Get competitor list in correct order /competition

# update Competitor (weight, record, attempt1-4)


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
            return redirect("/")

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
    return redirect("/")


@app.route("/", methods=["GET"])
def home():
    competitors = None

    competitors = Competitor.query.order_by(Competitor.order).all()
    weight_classes = WeightClass.query.all()
    return render_template("home.html", competitors=competitors, weight_classes=weight_classes) 

if __name__ == "__main__":
    app.run(debug=True)
