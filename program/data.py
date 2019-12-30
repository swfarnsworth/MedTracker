import datetime

import pytz
import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker

engine = sql.create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class Timezone(Base):
    """Stores the user's timezone"""
    __tablename__ = 'timezones'
    account_id = sql.Column(sql.String, primary_key=True)
    timezone = sql.Column(sql.String)

    def __repr__(self):
        return f"Timezome({self.account_id}, {self.timezone})"


class Med(Base):
    """Table for all medications tracked by the program"""
    __tablename__ = 'medications'
    account_id = sql.Column(sql.String, primary_key=True)
    name = sql.Column(sql.String, primary_key=True)
    when_taken = sql.Column(sql.Float)

    def take(self):
        """Sets self.when_taken to the Unix timestamp of the present time."""
        session = Session()
        # Get the user's timezone from the table of timezones; if it's there, get the name of it or set it to UTC
        user_timezone_entry = session.query(Timezone).filter_by(account_id=self.account_id).first()  # table entry
        user_timezone_name = user_timezone_entry.timezone if user_timezone_entry is not None else 'UTC'  # timezone str
        session.close()
        user_timezone = pytz.timezone(user_timezone_name)  # timezone object
        self.when_taken = datetime.datetime.now().astimezone(user_timezone).timestamp()

    def is_taken_today(self):
        """Returns True if this med was taken today"""
        session = Session()
        # Get the user's timezone from the table of timezones; if it's there, get the name of it or set it to UTC
        user_timezone_entry = session.query(Timezone).filter_by(account_id=self.account_id).first()  # table entry
        user_timezone_name = user_timezone_entry.timezone if user_timezone_entry is not None else 'UTC'  # timezone str
        session.close()
        user_timezone = pytz.timezone(user_timezone_name)  # timezone object
        when_taken = datetime.datetime.fromtimestamp(self.when_taken)
        return when_taken.astimezone(user_timezone).date() == datetime.datetime.today().astimezone(user_timezone).date()

    def __repr__(self):
        return f"Med({self.account_id}, {self.name}, {self.when_taken})"


Med.__table__.create(bind=engine)
Timezone.__table__.create(bind=engine)


def has_account(user_name):
    """Returns True if the user has at least one medication"""
    session = Session()
    num_meds = session.query(Med).filter_by(account_id=user_name).count()
    session.close()
    return num_meds > 0


def get_med(session, user_name, med_name):
    """Returns the first med with a matching user name and med name (there should only be one anyway)"""
    return session.query(Med).filter_by(account_id=user_name, name=med_name).first()


timezone_names = {}
for name in pytz.common_timezones:
    if "/" not in name:
        timezone_names[name.lower()] = name
    else:
        timezone_names[name.split("/")[1].lower()] = name


def set_timezone(user_name, user_tz_name):
    session = Session()
    underscore_tz_name = user_tz_name.replace(" ", "_").lower()
    timezone_name = timezone_names[underscore_tz_name]
    if timezone_name not in pytz.common_timezones:
        return False

    user_timezone = session.query(Timezone).filter_by(account_id=user_name).first()
    if not user_timezone:
        # User timezone has never been set
        timezone_column = Timezone(account_id=user_name, timezone=timezone_name)
        session.add(timezone_column)
    else:
        # Change user timezone
        user_timezone.timezone = timezone_name

    session.commit()
    return True
