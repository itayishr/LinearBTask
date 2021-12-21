from math import ceil
from flask import Flask, request, jsonify

# Create the flask application and configure its Database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///atm-db'

# Import the built models for the ATM and Currency tables
from models import Atm, db, Currencies


@app.before_first_request
# This method will seed a default databse into the ATM and add a default ILS currency
def seed_table():
    # Clean the table before seeding default data
    Atm.query.delete()

    # Add the ILS currency
    currency_to_add = Currencies("ILS")
    db.session.add(currency_to_add)
    db.session.commit()

    # Create the example currency and add it to db
    money_to_add = [Atm("BILL", 200, 0),
                    Atm("BILL", 100, 0),
                    Atm("BILL", 20, 0),
                    Atm("COIN", 10, 0),
                    Atm("COIN", 5, 0),
                    Atm("COIN", 1, 0),
                    Atm("COIN", 0.1, 0),
                    Atm("COIN", 0.01, 50)]

    for money in money_to_add:
        db.session.add(money)
        db.session.commit()


'''
The withdrawal API -
The consumer submits a request with the amount and currency,
the logic checks the DB for existing money and returns a result accordingly.
'''


@app.route('/atm/withdrawal', methods=['POST'])
def withdraw():
    class TooMuchCoinsException(Exception):
        pass

    """
    An internal logic that returns the required money to return in 
    the biggest bills existing, or passes a TooMuchCoinsException if
    result requires 50 coins or more.
    """

    def calculate_change(money, amount_to_withdraw):
        # Sort the money list in reverse, in order to return biggest bills possible.
        money_keys = sorted(money.keys(), reverse=True)
        # A counter for coins, checks if surpassed the 49 coin limit.
        count_coins = 0
        for key in money_keys:
            # If bill is not available, continue.
            if money[key]["amount"] == 0 or key > amount_to_withdraw:
                continue

            div_result = ceil(amount_to_withdraw / key)
            if div_result <= money[key]["amount"]:
                amount_to_withdraw = round(amount_to_withdraw - div_result * key, 2)
                money[key]["amount"] = money[key]["amount"] - div_result

                # After reaching result, reduce the required amount from ATM.
                money_to_update = Atm.query.filter_by(value=key).first()
                setattr(money_to_update, "amount", money[key]["amount"])
                db.session.commit()

                # Update the suitable list for money needed - bills or coins.
                if money[key]["type"] == "BILL":
                    bills[str(int(key))] = div_result
                else:
                    count_coins = count_coins + div_result
                    if key < 1:
                        key_name = str(key)
                    else:
                        key_name = str(int(key))
                    coins[key_name] = div_result

            # Check if calculation is done.
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
    1. Query the Currency table to check if required currency exists,
    and ATM for the required money.
    2. Calculate the amount of bills needed for transaction,
    use biggest bills available.
    3. If feasible, subtract bills from inventory and update DB
    4. Send back result to user
    """

    required_currency = request.args.get("currency")
    required_amount = request.args.get("amount")

    if required_currency and required_amount:
        currency_entry = Currencies.query.filter_by(value=required_currency)
        if currency_entry is None:
            return "No such currency in ATM", 400
        amount_tmp = round(float(required_amount), 2)
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


'''
The currency API -
This is an admin API that allows addition of new coins to the database.
'''


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
