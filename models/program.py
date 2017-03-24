from model import db


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
