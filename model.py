"""Models and database functions for webapp."""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.schema import UniqueConstraint

# Instantiate database
db = SQLAlchemy()


##############################################################################
# Model definitions
class ProgramType(db.Model):
    """."""

    __tablename__ = "program_types"

    type_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    program_type = db.Column(db.String(20), nullable=False, unique=True)

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<action {}: {}>".format(self.type_id,
                                        self.program_type,
                                        )


class Action(db.Model):
    """."""

    __tablename__ = "actions"

    action_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    action_type = db.Column(db.String(20), nullable=False, unique=True)

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
    type_id = db.Column(db.Integer, db.ForeignKey('program_types.type_id'), nullable=False)
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

    def user_outgoing(self):
        """Return all distinct programs that are outgoing in ratios table."""

        outgoing = db.session.query(Ratio)\
                             .distinct(Ratio.outgoing_program)\
                             .join(Balance, Balance.program_id == Ratio.outgoing_program)\
                             .filter(Balance.user_id == self.user_id).all()

        return outgoing

    def user_outgoing_collection(self, program_id):
        """Return all distinct programs that are outgoing in ratios table in collection of instances."""

        balance = self.get_balance_first(program_id)
        optimize = {
            "display_program": {},
            "outgoing": {}
        }

        if balance:
            optimize["display_program"]["balance"] = balance.current_balance
            optimize["display_program"]["program_name"] = balance.program.program_name
        else:
            optimize["display_program"]["balance"] = 0
            optimize["display_program"]["program_name"] = Program.query.get(program_id).program_name

        outgoing = self.user_outgoing()

        if self.user_outgoing():
            for program in outgoing:
                optimize["outgoing"][program.outgoing_program] = {"program_name": program.outgoing.program_name,
                                                                  "balance": self.get_balance(program.outgoing_program).current_balance
                                                                  }

        return optimize

    def user_receiving(self):
        """Return all distinct programs that are receiving in ratios table."""

        receiving = db.session.query(Ratio)\
                              .distinct(Ratio.receiving_program)\
                              .join(Balance, Balance.program_id == Ratio.receiving_program)\
                              .filter(Balance.user_id == self.user_id).all()

        return receiving

    def user_receiving_for(self, outgoing_id):
        """Given an outgoing program, return all distinct programs that are receiving in ratios table."""

        receiving = Ratio.query.filter(Ratio.outgoing_program == outgoing_id)\
                               .distinct(Ratio.receiving_program)\
                               .join(Balance, Balance.program_id == Ratio.receiving_program)\
                               .filter(Balance.user_id == self.user_id).all()
        return receiving

    def user_outgoing_for(self, receiving_id):
        """Given a receiving program, return all programs that are outgoing in ratios table."""

        outgoing = db.session.query(Ratio)\
                             .join(Balance, Balance.program_id == Ratio.outgoing_program)\
                             .filter((Balance.user_id == self.user_id) & (Ratio.receiving_program == receiving_id))\
                             .all()

        return outgoing

    def get_balance(self, program_id):
        """Given a program id, return the balance instance"""

        balance = Balance.query.filter((Balance.user_id == self.user_id) & (Balance.program_id == program_id)).one()

        return balance

    def get_balance_first(self, program_id):
        """Given a program id, return the balance instance"""

        balance = Balance.query.filter((Balance.user_id == self.user_id) & (Balance.program_id == program_id)).first()

        return balance

    def get_transactions(self):
        """ Return all transactions for a given user *activity.html """

        transactions = TransactionHistory.query.options(db.joinedload('program'))\
                                               .filter_by(user_id=self.user_id)\
                                               .order_by('created_at DESC')\
                                               .all()

        return transactions

    def get_transfers(self):
        """ Return all transactions for a given user *activity.html """

        transfers = Transfer.query.filter_by(user_id=self.user_id)\
                                  .join(Ratio, Ratio.outgoing_program == Transfer.outgoing_program)\
                                  .order_by('transferred_at DESC')\
                                  .all()

        return transfers


class Ratio(db.Model):
    """Transfer ratios between two programs."""

    __tablename__ = "ratios"
    __table_args__ = (
        UniqueConstraint('outgoing_program', 'receiving_program', name='directed_flow'),
    )

    ratio_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    outgoing_program = db.Column(db.Integer, db.ForeignKey('programs.program_id'), nullable=False)
    receiving_program = db.Column(db.Integer, db.ForeignKey('programs.program_id'), nullable=False)
    numerator = db.Column(db.Numeric, nullable=False)
    denominator = db.Column(db.Numeric, nullable=False)

    outgoing = db.relationship("Program", primaryjoin="Ratio.outgoing_program==Program.program_id")
    receiving = db.relationship("Program", primaryjoin="Ratio.receiving_program==Program.program_id")

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<ratio of [program {}] {} to [program {}] {} = {} / {}>".format(self.outgoing_program,
                                                                                self.outgoing.program_name,
                                                                                self.receiving_program,
                                                                                self.receiving.program_name,
                                                                                self.numerator,
                                                                                self.denominator,
                                                                                )

    def ratio_to(self):
        """Provide numerical ratio of numerator / denominator"""

        ratio = float(self.numerator) / float(self.denominator)

        return ratio


class Balance(db.Model):
    """Balance a user has at program."""

    __tablename__ = "balances"

    balance_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    action_id = db.Column(db.Integer, db.ForeignKey('actions.action_id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.program_id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    current_balance = db.Column(db.Integer, nullable=False)

    user = db.relationship('User', backref=db.backref('balances', order_by=program_id))
    program = db.relationship('Program', backref=db.backref('balances', order_by=balance_id))
    action = db.relationship('Action', backref=db.backref('balances', order_by=balance_id))

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<{} |user: {} |program: {} | balance: {} | {}>".format(self.balance_id,
                                                                       self.user_id,
                                                                       self.program.program_name,
                                                                       self.current_balance,
                                                                       self.updated_at,
                                                                       )

    def transferred_to(self, amount, ratio):
        """Update balance to receiving program balance after transfer."""

        self.current_balance = self.current_balance + amount * ratio
        self.action_id = Action.query.filter(Action.action_type == 'Transfer').one().action_id

    def transferred_from(self, amount):
        """Update balance to outgoing program balance after transfer."""

        self.current_balance = self.current_balance - amount
        self.action_id = Action.query.filter(Action.action_type == 'Transfer').one().action_id


class TransactionHistory(db.Model):
    """Transactions that impact program balance."""

    __tablename__ = "transaction_history"

    transaction_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    action_id = db.Column(db.Integer, db.ForeignKey('actions.action_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.program_id'), nullable=False)
    beginning_balance = db.Column(db.Integer, nullable=False)
    ending_balance = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', backref=db.backref('transaction_history'))
    program = db.relationship('Program', backref=db.backref('transaction_history'))
    action = db.relationship('Action', backref=db.backref('transaction_history'))

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<{} |user: {} |program: {} | beg: {} end: {} | {}>".format(self.transaction_id,
                                                                           self.user_id,
                                                                           self.program_id,
                                                                           self.beginning_balance,
                                                                           self.ending_balance,
                                                                           self.created_at,
                                                                           )


class Transfer(db.Model):
    """Transfers between two programs."""

    __tablename__ = "transfers"

    transfer_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    transferred_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    outgoing_program = db.Column(db.Integer, db.ForeignKey('programs.program_id'), nullable=False)
    receiving_program = db.Column(db.Integer, db.ForeignKey('programs.program_id'), nullable=False)
    outgoing_amount = db.Column(db.Integer, nullable=False)

    outgoing = db.relationship("Program", primaryjoin="Transfer.outgoing_program==Program.program_id")
    receiving = db.relationship("Program", primaryjoin="Transfer.receiving_program==Program.program_id")

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<{} |user: {} |program: {} to program: {}| amount: {} | {}>".format(self.transfer_id,
                                                                                    self.user_id,
                                                                                    self.outgoing_program,
                                                                                    self.receiving_program,
                                                                                    self.outgoing_amount,
                                                                                    self.transferred_at,
                                                                                    )


class Feedback(db.Model):
    """."""

    __tablename__ = "feedback"

    feedback_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    addressed = db.Column(db.Boolean, default=False, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('feedback_categories.category_id'), nullable=False)
    new_vendor_name = db.Column(db.String(32))
    new_program_name = db.Column(db.String(32))
    outgoing_name = db.Column(db.String(32))
    receiving_name = db.Column(db.String(32))
    new_numerator = db.Column(db.Integer)
    new_denominator = db.Column(db.Integer)
    feedback = db.Column(db.Text, nullable=False)

    user = db.relationship('User', backref=db.backref('feedback'))
    user = db.relationship('FeedbackCategory', backref=db.backref('feedback'))

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<from {}: {}>".format(self.email,
                                      self.feedback,
                                      )


class FeedbackCategory(db.Model):
    """."""

    __tablename__ = "feedback_categories"

    category_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    category_name = db.Column(db.String(60))

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<from {}: {}>".format(self.category_id,
                                      self.category_name,
                                      )


##############################################################################
# Helper functions

def ratio_instance(outgoing_id, receiving_id):
    """Given the outgoing and receiving program ids, return Ratio Instance"""

    return Ratio.query.filter((Ratio.outgoing_program == outgoing_id) & (Ratio.receiving_program == receiving_id)).first()


def add_transfer(user_id, outgoing_id, receiving_id, transfer_amount):
    """ Convenient transfer wrapper """

    transfer = Transfer(user_id=user_id, outgoing_program=outgoing_id, receiving_program=receiving_id, outgoing_amount=transfer_amount)
    db.session.add(transfer)

    return transfer


def add_balance(user_id, program_id, current_balance):
    """ Convenient add_balance wrapper """

    action_id = Action.query.filter(Action.action_type == 'New').one().action_id
    balance = Balance(user_id=user_id, program_id=program_id, current_balance=current_balance, action_id=action_id)
    db.session.add(balance)

    return balance


def add_user(email, password, fname, lname):
    """ Convenient registration wrapper """

    user = User(email=email, password=password, fname=fname, lname=lname)
    db.session.add(user)

    return user


def add_feedback(category_id,
                 email,
                 user_id=None,
                 vendor=None,
                 program=None,
                 outgoing=None,
                 receiving=None,
                 numerator=None,
                 denominator=None,
                 feedback_content=None):
    """ Convenient feedback wrapper """

    feedback = Feedback(email=email,
                        user_id=user_id,
                        category_id=category_id,
                        new_vendor_name=vendor,
                        new_program_name=program,
                        outgoing_name=outgoing,
                        receiving_name=receiving,
                        new_numerator=numerator,
                        new_denominator=denominator,
                        feedback=feedback_content,
                        )

    db.session.add(feedback)
    db.session.commit()

    return


def mapping(user_id=None):

    all_programs = {}
    i = 0

    mapping = {
        "nodes": [],
        "links": []
    }

    if user_id:
        user = User.query.get(user_id)
        outgoing = user.user_outgoing()
        receiving = user.user_receiving()

        for program in receiving:
            if program.receiving_program not in all_programs:
                all_programs[program.receiving_program] = i
                i += 1
                mapping["nodes"].append({"name": program.receiving.program_name,
                                         "group": program.receiving.type_id,
                                         "img": program.receiving.vendor.img})

        for program_from in outgoing:
            if program_from.outgoing_program not in all_programs:
                all_programs[program_from.outgoing_program] = i
                i += 1
                mapping["nodes"].append({"name": program_from.outgoing.program_name,
                                         "group": program_from.outgoing.type_id,
                                         "img": program_from.outgoing.vendor.img})

            for program_to in receiving:
                ratio = ratio_instance(program_from.outgoing_program, program_to.receiving_program)
                if ratio:
                    mapping["links"].append({"source": all_programs[ratio.outgoing_program],
                                             "target": all_programs[ratio.receiving_program],
                                             "value": 1})

    else:
        outgoing = db.session.query(Ratio).distinct(Ratio.outgoing_program).all()
        receiving = db.session.query(Ratio).distinct(Ratio.receiving_program).all()
        ratios = db.session.query(Ratio).join(Program, Program.program_id == Ratio.outgoing_program).all()

        for program in outgoing:
            if program.outgoing_program not in all_programs:
                all_programs[program.outgoing_program] = i
                i += 1
                mapping["nodes"].append({"name": program.outgoing.program_name,
                                         "group": program.outgoing.type_id,
                                         "img": program.outgoing.vendor.img})

        for program in receiving:
            if program.receiving_program not in all_programs:
                all_programs[program.receiving_program] = i
                i += 1
                mapping["nodes"].append({"name": program.receiving.program_name,
                                         "group": program.receiving.type_id,
                                         "img": program.receiving.vendor.img})

        for ratio in ratios:
            mapping["links"].append({"source": all_programs[ratio.outgoing_program],
                                     "target": all_programs[ratio.receiving_program],
                                     "value": 1})

    return mapping


##############################################################################
# Sub-Helper functions

def init_app():
    # So that we can use Flask-SQLAlchemy, we'll make a Flask app.
    from flask import Flask
    app = Flask(__name__)

    connect_to_db(app)
    print "Connected to DB."


def connect_to_db(app, db_uri=None):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri or 'postgres:///koi'
    app.config['SQLALCHEMY_ECHO'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.
    from server import app

    connect_to_db(app)
    print "Connected to DB."
