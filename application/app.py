from flask import Flask, request, render_template, jsonify
from flask.cli import with_appcontext

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///atm-db'

from models import AtmEntry, db


@app.before_first_request
def seed_table():
    AtmEntry.query.delete()
    new_entries = [AtmEntry("BILL", 200, 7),
                   AtmEntry("BILL", 100, 4),
                   AtmEntry("COIN", 10, 0),
                   AtmEntry("COIN", 5, 1),
                   AtmEntry("COIN", 0.1, 12),
                   AtmEntry("COIN", 0.01, 21)]
    for new_entry in new_entries:
        db.session.add(new_entry)
        db.session.commit()


@app.route('/atm/withdrawal', methods=['POST'])
def withdraw():
    type = request.args.get("type")
    value = request.args.get("value")
    amount = request.args.get("amount")
    if type and value and amount:
        # new_entry = AtmEntry(type, value, amount)
        # db.session.add(new_entry)
        # db.session.commit()
        query = AtmEntry.query.all()
        payload = []
        for result in query:
            content = {"type": result.type, "value": result.value, "amount": result.amount}
            payload.append(content)
            content = {}
        return jsonify(payload)


@app.route('/admin/currency', methods=['POST'])
def currency():
    return


if __name__ == '__main__':
    # db.create_all()
    db.init_app(app)
    app.run(debug=True)
