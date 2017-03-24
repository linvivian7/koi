from model import db
from ratio import Ratio
from balance import Balance
from program import Program
from transaction_history import TransactionHistory
from transfer import Transfer
from program import Vendor


class User(db.Model):
    """Users."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    fname = db.Column(db.String(32), nullable=False)
    lname = db.Column(db.String(32), nullable=False)
    is_email_confirmed = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<user {}: {} {} email={}>".format(self.user_id,
                                                  self.fname,
                                                  self.lname,
                                                  self.email,
                                                  )

    def user_outgoing(self):
        """Return all distinct programs that are outgoing in ratios table."""

        User.query.options(db.joinedload('balances'))

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

    def delete_balance(self, program_id):
        """Given a program id, delete the balance instance"""

        balance = self.get_balance(program_id)

        db.session.delete(balance)
        db.session.commit()

    def program_balances(self):
        balances = db.session.query(Balance.program_id,
                                    Vendor.vendor_name,
                                    Program.program_name,
                                    Balance.updated_at,
                                    Balance.current_balance, Vendor.vendor_name)\
            .join(Program)\
            .join(Vendor)\
            .filter(Balance.user_id == self.user_id).all()

        return balances

    def get_balances(self):
        base = Balance.query.filter_by(user_id=self.user_id).options(db.joinedload('program'))
        balances = base.all()

        return balances

    def get_balances_count(self):
        count = Balance.query.filter_by(user_id=self.user_id).options(db.joinedload('program')).count()

        return count

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

    @staticmethod
    def confirm_user(email):
        user = User.query.filter_by(email=email).first()

        user.is_email_confirmed = True

        db.session.add(user)
        db.session.commit()


def add_user(email, password, fname, lname):
    """ Convenient registration wrapper """

    user = User(email=email, password=password, fname=fname, lname=lname)
    db.session.add(user)
    db.session.commit()

    return user
