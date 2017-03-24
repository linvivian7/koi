from model import db
from action import Action


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


def add_balance(user_id, program_id, current_balance):
    """ Convenient add_balance wrapper """

    action_id = Action.query.filter(Action.action_type == 'New').one().action_id
    balance = Balance(user_id=user_id, program_id=program_id, current_balance=current_balance, action_id=action_id)
    db.session.add(balance)

    return balance
