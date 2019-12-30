from flask import Flask, request
from flask_ask import Ask, statement, question

import data as db


app = Flask(__name__)
ask = Ask(app, '/')


def get_id(req):
    """Gets the Amazon account ID of the requesting user"""
    incoming_json = req.get_json()
    user_id = incoming_json["context"]["System"]["user"]["userId"]
    return user_id


@ask.launch
def on_launch():
    """Runs if the user invokes the program without specifying an intent"""
    return statement("Thank you for trying medication tracker!")


@ask.on_session_started
def before_starting():
    """Runs before any of the intent methods; checks that the user has
    an account before continuing with the session."""
    incoming_json = request.get_json()
    user_id = get_id(incoming_json)
    if not db.has_account(user_id):
        return question("This appears to be your first time using Medication Tracker. I have created an account "
                        "for you. Please repeat your request and we will get started.")


@ask.intent("AMAZON.FallbackIntent")
def fallback_intent():
    return statement("Sorry, med tracker didn't understand that.")


@ask.intent("TakeMedIntent", mapping={"med_name": "Med"})
def take_med_intent(med_name):
    session = db.Session()
    user_id = get_id(request)

    med = db.get_med(session, user_id, med_name)

    if not med:
        session.close()
        return statement(f"I'm not tracking {med_name}. Let me know if you want to start tracking it.")

    med.take()
    session.commit()
    return statement(f"Okay, you've taken {med_name}.")



@ask.intent("TakeTwoMedIntent", mapping={"med_name": "Med",
                                         "med_name_2": "MedTwo"})
def take_two_med_intent(med_name, med_name_2):
    """Tell the skill you want to take a med"""
    session = db.Session()
    user_id = get_id(request)
    med_names = [med_name, med_name_2]

    meds = [db.get_med(session, user_id, med) for med in med_names]

    if not all(meds):
        session.close()
        return statement("I didn't recognize one of those medications, so I didn't record anything")

    for med in meds:
        med.take()

    session.commit()
    return statement(f"Okay, you've taken {med_name} and {med_name_2}")


@ask.intent("TakeThreeMedIntent", mapping={"med_name": "Med",
                                           "med_name_2": "MedTwo",
                                           "med_name_3": "MedThree"})
def take_three_med_intent(med_name, med_name_2, med_name_3):
    """Tell the skill you want to take three meds"""
    session = db.Session()
    user_id = get_id(request)
    med_names = [med_name, med_name_2, med_name_3]

    meds = [db.get_med(session, user_id, med) for med in med_names]

    if not all(meds):
        session.close()
        return statement("I didn't recognize one of those medications, so I didn't record anything")

    for med in meds:
        med.take()

    session.commit()
    return statement(f"Okay, you've taken {med_name}, {med_name_2}, and {med_name_3}")


@ask.intent("AddMedIntent", mapping={"med_name": "Med"})
def add_med_intent(med_name):
    """Tell the skill to add a med to your account"""
    session = db.Session()
    user_id = get_id(request)

    # See if the med is already there
    med = db.get_med(session, user_id, med_name)

    if med:
        return statement(f"I'm already tracking {med_name} for you.")

    new_med = db.Med(account_id=user_id, name=med_name, when_taken=0.0)
    session.add(new_med)
    session.commit()

    return statement(f"I'm now tracking {med_name} for you")


@ask.intent("RemoveMedIntent", mapping={"med_name": "Med"})
def remove_med_intent(med_name):
    """Tell the skill to remove a med from your account"""
    session = db.Session()
    user_id = get_id(request)

    med = db.get_med(session, user_id, med_name)

    if not med:
        session.close()
        return statement(f"I wasn't tracking {med_name}.")

    session.delete(med)
    session.commit()

    return statement(f"I'm no longer keeping track of {med_name}.")


@ask.intent("AskMedIntent", mapping={"med_name": "Med"})
def ask_med_intent(med_name):
    """Ask the skill if you took a med"""
    session = db.Session()
    user_id = get_id(request)

    med = db.get_med(session, user_id, med_name)

    if not med:
        session.close()
        return statement(f"I'm not tracking {med_name}.")


    is_taken = med.is_taken_today()
    session.close()

    if is_taken:
        return statement(f"You did take {med_name}")
    else:
        return statement(f"You haven't taken {med_name} today")


@ask.intent("CancelMedIntent", mapping={"med_name": "Med"})
def cancel_med_intent(med_name):
    """Tell the skill that you didn't actually take a med"""
    session = db.Session()
    user_id = get_id(request)

    med = db.get_med(session, user_id, med_name)

    if not med:
        session.close()
        return statement(f"I wasn't tracking {med_name}.")

    taken_today = med.is_taken_today()

    if not taken_today:
        session.close()
        return statement(f"It seems you didn't take {med_name} anyway.")

    med.when_taken = 0.0
    session.commit()
    return statement(f"Okay, you didn't take {med_name}")


@ask.intent("WhatMedsTakenIntent")
def what_meds_taken_intent():
    """State which meds have been taken"""
    session = db.Session()
    user_id = get_id(request)
    meds = session.query(db.Med).filter_by(account_id=user_id)

    if not meds:
        session.close()
        return statement("I'm not tracking any medications for you.")

    meds_taken = [m.name for m in meds if m.is_taken_today()]
    session.close()

    if len(meds_taken) == 0:
        return statement("You haven't told me that you've taken any medications.")
    if len(meds_taken) == 1:
        return statement(f"You've told me that you've taken {meds_taken[0]}")
    if len(meds_taken) == 2:
        return statement(f"You've told me that you've taken {meds_taken[0]} and {meds_taken[1]}")
    if len(meds_taken) > 2:
        return_statement = "You've told me that you've taken " + ", ".join(meds_taken[:-1]) + f", and {meds_taken[-1]}"
        return statement(return_statement)


@ask.intent("SetTimezoneIntent", mapping={"timezone_name": "Timezone"})
def set_timezone_intent(timezone_name):
    """Set the user's timezone"""
    user_id = get_id(request)
    if db.set_timezone(user_id, timezone_name):
        return statement(f"Your timezone has been set to {timezone_name}")
    else:
        return statement(f"{timezone_name} is not a valid timezone name")


if __name__ == "__main__":
    app.run()
