"""
Deletes all accounts from the database that have not been accessed in over six months
"""

import program.data as db


def main():
    """Delete all data for users who have not used the app in > 6 months"""
    SIX_MONTHS = 1.577e7
    session = db.Session()
    accounts_to_del = [acc for acc in session.query(db.User).all() if acc.get_time_since_last_use() > SIX_MONTHS]

    meds_to_del = []
    for acc in accounts_to_del:
        acc_name = acc.account_id
        meds_to_del += session.query(db.Med).filter_by(account_id=acc_name).all()

    for item in accounts_to_del + meds_to_del:
        session.delete(item)

    session.commit()


if __name__ == '__main__':
    main()