import sys
import traceback
from math import ceil

from flask import Flask, request, render_template, jsonify
from forex_python.converter import CurrencyRates

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///atm-db'

from models import AtmEntry, db


@app.before_first_request
def seed_table():
    AtmEntry.query.delete()
    new_entries = [AtmEntry("BILL", 200, 7),
                   AtmEntry("BILL", 100, 4),
                   AtmEntry("BILL", 20, 1),
                   AtmEntry("COIN", 10, 1),
                   AtmEntry("COIN", 5, 1),
                   AtmEntry("COIN", 1, 10),
                   AtmEntry("COIN", 0.1, 12),
                   AtmEntry("COIN", 0.01, 50)]
    new_entries = [AtmEntry("BILL", 200, 0),
                   AtmEntry("BILL", 100, 0),
                   AtmEntry("BILL", 20, 0),
                   AtmEntry("COIN", 10, 0),
                   AtmEntry("COIN", 5, 0),
                   AtmEntry("COIN", 1, 0),
                   AtmEntry("COIN", 0.1, 0),
                   AtmEntry("COIN", 0.01, 50)]
    for new_entry in new_entries:
        db.session.add(new_entry)
        db.session.commit()


@app.route('/atm/withdrawal', methods=['POST'])
def withdraw():
    class TooMuchCoinsException(Exception):
        pass

    def calculate_change(money, amount_to_withdraw):
        money_keys = sorted(money.keys(), reverse=True)
        count_coins = 0
        for key in money_keys:
            if money[key]["amount"] == 0 or key > amount_to_withdraw:
                continue
            div_result = ceil(amount_to_withdraw / key)
            if div_result <= money[key]["amount"]:
                amount_to_withdraw = round(amount_to_withdraw - div_result * key, 2)
                money[key]["amount"] = money[key]["amount"] - div_result
                money_to_update = AtmEntry.query.filter_by(value=key).first()
                setattr(money_to_update, "amount", money[key]["amount"])
                db.session.commit()
                if money[key]["type"] == "BILL":
                    bills[str(int(key))] = div_result
                else:
                    count_coins = count_coins + div_result
                    if key < 1:
                        key_name = str(key)
                    else:
                        key_name = str(int(key))
                    coins[key_name] = div_result
            if amount_to_withdraw % key == 0:
                break
        if amount_to_withdraw != 0:
            return None
        if count_coins >= 50:
            raise TooMuchCoinsException("Too many coins for withdrawal")
        else:
            final_result = {"result": {"bills": [bills], "coins": [coins]}}
            return final_result

    """
    Logic steps:
    1. Query the atm table and the money that exists for currency
    2. Calculate the amount of bills needed for transaction,
    use biggest bills available.
    3. If feasible, subtract bills from inventory and update DB
    4. Send back result to user
    """
    # currency = request.args.get("type")
    amount = request.args.get("amount")
    exchange_rate = 1
    if currency and amount:
        amount_tmp = round(float(amount), 2)
        # Check if currency exists in ATM
        entries = AtmEntry.query.all()
        money = dict()
        bills = dict()
        coins = dict()
        if entries is None:
            return "ATM Empty, please try again later.", 400
        for entry in entries:
            money[entry.value] = {"type": entry.type, "amount": entry.amount}
        try:
            result = calculate_change(money, amount_tmp)
        except TooMuchCoinsException as e:
            return jsonify({'TooMuchCoinsException':str(e)})
        if result is None:
            return "Insufficient change for withdrawal", 400
        else:
            return jsonify(result)


@app.route('/admin/currency', methods=['POST'])
def currency():
    return


if __name__ == '__main__':
    # db.create_all()
    db.init_app(app)
    app.run(debug=True)
