from model import db


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
