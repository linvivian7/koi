from model import db


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


def add_transfer(user_id, outgoing_id, receiving_id, transfer_amount):
    """ Convenient transfer wrapper """

    transfer = Transfer(user_id=user_id, outgoing_program=outgoing_id, receiving_program=receiving_id, outgoing_amount=transfer_amount)
    db.session.add(transfer)

    return transfer
