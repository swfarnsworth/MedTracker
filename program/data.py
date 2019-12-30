import datetime

import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker

engine = sql.create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class Med(Base):
    """Table for all medications tracked by the program"""
    __tablename__ = 'medications'
    account_id = sql.Column(sql.String, primary_key=True)
    name = sql.Column(sql.String, primary_key=True)
    when_taken = sql.Column(sql.Float)

    def take(self):
        """Sets self.when_taken to the Unix timestamp of the present time."""
        self.when_taken = datetime.datetime.now().timestamp()

    def is_taken_today(self):
        """Returns True if this med was taken today"""
        when_taken = datetime.datetime.fromtimestamp(self.when_taken)
        return when_taken.date() == datetime.datetime.today().date()

    def __repr__(self):
        return f"Med({self.account_id}, {self.name}, {self.when_taken})"


Med.__table__.create(bind=engine)


def has_account(user_name):
    """Returns True if the user has at least one medication"""
    session = Session()
    num_meds = session.query(Med).filter_by(account_id=user_name).count()
    session.close()
    return num_meds > 0


def get_med(session, user_name, med_name):
    """Returns the first med with a matching user name and med name (there should only be one anyway)"""
    return session.query(Med).filter_by(account_id=user_name, name=med_name).first()
