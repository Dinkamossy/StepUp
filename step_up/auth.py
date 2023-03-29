import functools
import re

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from step_up.database import get_database

bp = Blueprint('auth', __name__, url_prefix='/auth')


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        # Get today's date
        today = datetime.today().date()

        # Get elements from form
        username = request.form['username']
        password: str = request.form['password']
        email = request.form['email_address']

        database = get_database()
        error = None

        # we need a limit on these two
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        # Validate format of user's email address
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not email:
            error = 'Please enter your email address'
        elif not (re.fullmatch(email_regex, email)):
            error = "Invalid email address"

        if error is None:
            try:
                # Insert a new row into the DB with the new values
                # Hash the new password
                password = generate_password_hash(password)
                database.execute(
                    "INSERT INTO user (username, email, password, sex, race, age, feet, inches, "
                    "current_weight, target_weight, weight_circum, neck_circum, body_comp, steps) VALUES "
                    "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (username, email, password, 'male', 'other', '01-01-2000', 0, 0, 0, 0, 0, 0, 0, 0)
                )
                # Write the change to the database
                database.commit()
                flash('Account Created!')

            # Catch cases where a username already exists
            except (database.InternalError,
                    database.IntegrityError):
                error = f"User with username {username} already exists."
            else:
                return redirect(url_for("auth.patient_survey"))

        flash(error)
    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        database = get_database()
        error = None
        user = database.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        # If we are given a blank username, throw an error
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        # generates cookies for the logged-in user
        if error is None:
            session.clear()
            session['userid'] = user['userid']
            return redirect(url_for('mainpage'))

        flash(error)

    return render_template('auth/login.html')


@bp.route('/patient_survey', methods=('GET', 'POST'))
@login_required
def patient_survey(username):
    """
    Allows users to enter their information into the database
    """
    if request.method == 'POST':
        # Get security questions from the form
        sex = request.form['sex']
        race = request.form['race']
        age = request.form['age']
        feet = request.form['feet']
        inches = request.form['inches']
        userid = request.form['userid']
        current_weight = request.form['current_weight']
        target_weight = request.form['target_weight']
        weight_circum = request.form['weight_circum']
        neck_circum = request.form['neck_circum']
        body_comp = request.form['body_comp']

        # Get a handle on the database and set error value
        database = get_database()
        error = None

        # Verify Data todo(add more validation)
        if not sex:
            error = 'Please enter your sex'
        if not race:
            error = 'Please enter your race'
        if not age:
            error = 'Please enter your date of birth'
        elif age:
            try:
                correct_date = bool(datetime.strptime(age, "%m-%d-%Y"))
            except ValueError:
                correct_date = False
            if not correct_date:
                error = 'Date of birth must be formatted as MM-DD-YYYY'
        if not feet:
            error = 'Please enter your feet in height'
        if not inches:
            error = 'Please enter your inches in height'
        if not current_weight:
            error = 'Please enter your current weight'
        if not target_weight:
            error = 'Please enter your target weight'
        if not weight_circum:
            error = 'Please enter your weight circumference'
        if not neck_circum:
            error = 'Please enter your neck circumference'
        if not body_comp:
            error = 'Please enter your body composition percent'

        if error is None:
            try:
                # Change values in database
                database.execute(
                    "UPDATE user SET sex = ?, race = ?, age = ?, feet = ?, inches = ?,"
                    "current_weight = ?, target_weight = ?, weight_circum = ?, neck_circum = ?, body_comp = ? "
                    "WHERE username = ?",
                    (sex, race, age, feet, inches, current_weight, target_weight, weight_circum, neck_circum,
                     body_comp, g.user['username'])
                )
                database.commit()
            # Catch any errors
            except (database.InternalError,
                    database.IntegrityError):
                error = f"Unable to update survey"
            else:
                return redirect(url_for("auth.login"))
    # Tell the user it worked
    flash("Info updated!")
    # TODO Send user to dashboard when it's made
    return render_template('auth/patient_survey.html')


@bp.before_app_request
def load_logged_in_user():
    userid = session.get('userid')

    if userid is None:
        g.user = None
    else:
        g.user = get_database().execute(
            "SELECT * FROM user WHERE userid = ?", (userid,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('mainpage'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
