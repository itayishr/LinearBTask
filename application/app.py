from math import ceil

from flask import Flask, request, render_template, jsonify
from forex_python.converter import CurrencyRates

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///atm-db'

from models import Atm, db, Currencies


@app.before_first_request
def seed_table():
    Atm.query.delete()
    # new_entries = [Atm("BILL", 200, 7),
    #                Atm("BILL", 100, 4),
    #                Atm("BILL", 20, 1),
    #                Atm("COIN", 10, 1),
    #                Atm("COIN", 5, 1),
    #                Atm("COIN", 1, 10),
    #                Atm("COIN", 0.1, 12),
    #                Atm("COIN", 0.01, 50)]
    currency = Currencies("ILS")
    db.session.add(currency)
    db.session.commit()
    new_entries = [Atm("BILL", 200, 0),
                   Atm("BILL", 100, 0),
                   Atm("BILL", 20, 0),
                   Atm("COIN", 10, 0),
                   Atm("COIN", 5, 0),
                   Atm("COIN", 1, 0),
                   Atm("COIN", 0.1, 0),
                   Atm("COIN", 0.01, 50)]
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
                money_to_update = Atm.query.filter_by(value=key).first()
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
    currency = request.args.get("currency")
    amount = request.args.get("amount")
    if currency and amount:
        currency_entry = Currencies.query.filter_by(value=currency)
        if currency_entry is None:
            return "No such currency in ATM", 400
        amount_tmp = round(float(amount), 2)
        # Check if currency exists in ATM
        atm_entries = Atm.query.all()
        money = dict()
        bills = dict()
        coins = dict()
        if atm_entries is None:
            return "ATM Empty, please try again later.", 400
        for entry in atm_entries:
            money[entry.value] = {"type": entry.type, "amount": entry.amount}
        try:
            result = calculate_change(money, amount_tmp)
        except TooMuchCoinsException as e:
            return jsonify({'TooMuchCoinsException': str(e)})
        if result is None:
            return "Insufficient change for withdrawal", 400
        else:
            return jsonify(result)


@app.route('/admin/currency', methods=['POST'])
def currency():
    currency_to_add = request.args.get("currency")
    currency_entry = Currencies.query.filter_by(value=currency_to_add)
    if currency_entry is None:
        new_currency = Currencies(currency_to_add)
        db.add(new_currency)
        db.session.commit()


if __name__ == '__main__':
    db.init_app(app)
    app.run(debug=True)
