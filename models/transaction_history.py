from model import db


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

