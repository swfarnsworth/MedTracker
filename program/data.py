import datetime

import pytz
import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker


engine = sql.create_engine('sqlite:///./database.db', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class User(Base):
    """Stores the user's timezone"""
    __tablename__ = 'timezones'
    account_id = sql.Column(sql.String, primary_key=True)
    timezone = sql.Column(sql.String)
    last_used = sql.Column(sql.Float)

    def __repr__(self):
        return f"User({self.account_id}, {self.timezone}, {self.last_used})"

    def set_last_use(self):
        """Sets self.last_used to the current UTC time"""
        self.last_used = datetime.datetime.now().timestamp()

    def get_time_since_last_use(self):
        """Returns how many seconds since the user last used the program"""
        now = datetime.datetime.now().timestamp()
        return now - self.last_used


class Med(Base):
    """Table for all medications tracked by the program"""
    __tablename__ = 'medications'
    account_id = sql.Column(sql.String, primary_key=True)
    name = sql.Column(sql.String, primary_key=True)
    when_taken = sql.Column(sql.Float)

    def take(self):
        """Sets self.when_taken to the Unix timestamp of the present time."""
        timezone = self._get_timezone()
        self.when_taken = datetime.datetime.now().astimezone(timezone).timestamp()

    def is_taken_today(self):
        """Returns True if this med was taken today"""
        timezone = self._get_timezone()
        when_taken = datetime.datetime.fromtimestamp(self.when_taken)
        return when_taken.astimezone(timezone).date() == datetime.datetime.today().astimezone(timezone).date()

    def _get_timezone(self):
        """Returns a pytz.timezone object for the user's timezone"""
        session = Session()
        # Get the user's timezone from the table of timezones; if it's there, get the name of it or set it to UTC
        user_timezone_entry = session.query(User).filter_by(account_id=self.account_id).first()  # table entry
        user_timezone_name = user_timezone_entry.timezone if user_timezone_entry is not None else 'UTC'  # timezone str
        session.close()
        return pytz.timezone(user_timezone_name)

    def __repr__(self):
        return f"Med({self.account_id}, {self.name}, {self.when_taken})"


Med.__table__.create(bind=engine)
User.__table__.create(bind=engine)


def has_account(user_name, session=None):
    """Returns True if the user has at least one medication"""
    session = session or Session()
    account = session.query(User).filter_by(account_id=user_name).first()

    if account is None:
        new_account = User(last_used=0.0)
        session.add(new_account)
        session.commit()
        return False

    account.set_last_use()
    return True


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

    user_timezone = session.query(User).filter_by(account_id=user_name).first()
    if not user_timezone:
        # User timezone has never been set
        timezone_column = User(account_id=user_name, timezone=timezone_name)
        session.add(timezone_column)
    else:
        # Change user timezone
        user_timezone.timezone = timezone_name

    session.commit()
    return True
