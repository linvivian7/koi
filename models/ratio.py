from model import db
from sqlalchemy.schema import UniqueConstraint


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


def ratio_instance(outgoing_id, receiving_id):
    """Given the outgoing and receiving program ids, return Ratio Instance"""

    return Ratio.query.filter((Ratio.outgoing_program == outgoing_id) & (Ratio.receiving_program == receiving_id)).first()
