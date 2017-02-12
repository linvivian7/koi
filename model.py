"""Models and database functions for webapp."""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime, timedelta

# Instantiate database
db = SQLAlchemy()


##############################################################################
# Model definitions
class Action(db.Model):
    """."""

    __tablename__ = "actions"

    action_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    action_type = db.Column(db.String(32), nullable=False, unique=True)

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<action {}: {}>".format(self.action_id,
                                        self.action_type,
                                        )


class Vendor(db.Model):
    """Vendors with loyalty programs."""

    __tablename__ = "vendors"

    vendor_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    vendor_name = db.Column(db.String(32), nullable=False, unique=True)
    img = db.Column(db.String(255), nullable=True)
    url = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<vendor {}: {}>".format(self.vendor_id,
                                        self.vendor_name,
                                        )


class Program(db.Model):
    """All loyalty program."""

    __tablename__ = "programs"

    program_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.vendor_id'), nullable=False)
    program_name = db.Column(db.String(32), nullable=False, unique=True)

    vendor = db.relationship('Vendor', backref=db.backref('programs', order_by=program_id))

    def __repr__(self):
            """Provide helpful representation when printed."""

            return "<program {}: {} | vendor: {}>".format(self.program_id,
                                                          self.program_name,
                                                          self.vendor.vendor_id,
                                                          )


class User(db.Model):
    """Users."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    fname = db.Column(db.String(32), nullable=False)
    lname = db.Column(db.String(32), nullable=False)

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<user {}: {} {} email={}>".format(self.user_id,
                                                  self.fname,
                                                  self.lname,
                                                  self.email,
                                                  )


class Ratio(db.Model):
    """Transfer ratios between two programs."""

    __tablename__ = "ratios"
    __table_args__ = (
        UniqueConstraint('outgoing_program', 'receiving_program', name='directed_flow'),
    )

    ratio_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    outgoing_program = db.Column(db.Integer, db.ForeignKey('programs.program_id'), nullable=False)
    receiving_program = db.Column(db.Integer, db.ForeignKey('programs.program_id'), nullable=False)
    ratio = db.Column(db.Numeric, nullable=False)

    outgoing = db.relationship("Program", primaryjoin="Ratio.outgoing_program==Program.program_id")
    receiving = db.relationship("Program", primaryjoin="Ratio.receiving_program==Program.program_id")

    def __repr__(self):
            """Provide helpful representation when printed."""

            return "<ratio of [program {}] {} to [program {}] {} = {}>".format(self.outgoing_program,
                                                                               self.outgoing.program_name,
                                                                               self.receiving_program,
                                                                               self.receiving.program_name,
                                                                               self.ratio,
                                                                               )


class Balance(db.Model):
    """Balance a user has at program."""

    __tablename__ = "balances"

    balance_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.program_id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    current_balance = db.Column(db.Integer, nullable=False)
    action_id = db.Column(db.Integer, db.ForeignKey('actions.action_id'), nullable=False)

    user = db.relationship('User', backref=db.backref('balances', order_by=balance_id))
    program = db.relationship('Program', backref=db.backref('balances', order_by=balance_id))

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<{} |user: {} |program: {} | balance: {} | {}>".format(self.balance_id,
                                                                       self.user_id,
                                                                       self.program.program_name,
                                                                       self.current_balance,
                                                                       self.updated_at,
                                                                       )


class TransactionHistory(db.Model):
    """Transactions that impact program balance."""

    __tablename__ = "transaction_history"

    transaction_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    balance_id = db.Column(db.Integer, db.ForeignKey('balances.balance_id'), nullable=False)
    beginning_balance = db.Column(db.Integer, nullable=False)
    ending_balance = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    balance = db.relationship('Balance', backref=db.backref('transaction_history', order_by=transaction_id))

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<{} |user: {} |program: {} | beg: {} amount: {} end: {} | {}>".format(self.transaction_id,
                                                                                      self.balance.user_id,
                                                                                      self.balance.program_id,
                                                                                      self.beginning_balance,
                                                                                      self.ending_balance,
                                                                                      self.created_at,
                                                                                      )

    def calc_change(self):

        self.delta = self.ending_balance - self.beginning_balance

        return


class Transfer(db.Model):
    """Transfers between two programs."""

    __tablename__ = "transfers"

    transfer_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    transferred_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    outgoing_program = db.Column(db.Integer, db.ForeignKey('ratios.outgoing_program'), nullable=False)
    receiving_program = db.Column(db.Integer, db.ForeignKey('ratios.receiving_program'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)

    ratio_from = db.relationship("Ratio", primaryjoin="Transfer.outgoing_program==Ratio.outgoing_program")

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<{} |user: {} |program: {} to program: {}| amount: {} | {}>".format(self.transfer_id,
                                                                                    self.user_id,
                                                                                    self.outgoing_program,
                                                                                    self.receiving_program,
                                                                                    self.amount,
                                                                                    self.transferred_at,
                                                                                    )


##############################################################################
# Helper functions

def init_app():
    # So that we can use Flask-SQLAlchemy, we'll make a Flask app.
    from flask import Flask
    app = Flask(__name__)

    connect_to_db(app)
    print "Connected to DB."


def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///koi'
    app.config['SQLALCHEMY_ECHO'] = False
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.
    from server import app

    connect_to_db(app)
    print "Connected to DB."
