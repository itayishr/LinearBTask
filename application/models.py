from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class AtmEntry(db.Model):
    __tablename__ = 'atm'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(4), nullable=False)
    value = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Integer, nullable=False)

    def __init__(self, type, value, amount):
        self.type = type
        self.value = value
        self.amount = amount

    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}
