from model import db


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
