import functools
import re
from io import BytesIO

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from PIL import Image
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

            # Catch database errors
            except (database.InternalError,
                    database.IntegrityError):
                error = "Unexpected database issue."
            else:
                return redirect(url_for("auth.patient_survey"))
        flash(error)
    return redirect(url_for('mainpage'))


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
    return render_template('auth/patient_survey.html')


@bp.route('/my_account', methods=('GET', 'POST'))
@login_required
def my_account():
    """
     View to allow a user to edit information about their account (change password, upload photo, etc.)
     """

    if request.method == 'POST':
        # Get handle on DB
        database = get_database()
        # Get the info from the form fields
        username = request.form['username']
        email = request.form['email']
        uploaded_pic = request.files['uploaded_pic']
        # Make sure a picture was supplied
        if uploaded_pic.filename:
            # Ensure that the pic uploaded is of the correct type
            if uploaded_pic.mimetype not in ['image/jpeg', 'image/png']:
                flash("Improper profile picture format. Profile pictures must be JPEG or PNG")
                return redirect(url_for('auth.my_account'))
            # Ensure we know what type of image it is
            image_type = None
            if uploaded_pic.mimetype == 'image/jpeg':
                image_type = "JPEG"
            if uploaded_pic.mimetype == 'image/png':
                image_type = "PNG"
            # Open image using Pillow library for manipulation
            uploaded_pic = Image.open(uploaded_pic)
            # Resize the picture to save DB size
            uploaded_pic.thumbnail((200, 200))
            # Create a temporary byte buffer for the image
            temp_buffer = BytesIO()
            # Write the uploaded image to the temporary byte buffer
            uploaded_pic.save(temp_buffer, format=image_type)
            # Save the new image in the database
            uploaded_pic = temp_buffer.getvalue()
            database.execute(
                "UPDATE users SET picture = ?, email = ?, username = ? WHERE userid = ?",
                (uploaded_pic, email, username, g.user['userid'])
            )
            database.commit()
        else:
            database.execute(
                "UPDATE users SET email_address = ?, first_name = ?, last_name = ?, address = ? WHERE userid = ?",
                (email, username, g.user['userid'])
            )
            database.commit()
        # Tell the user it worked
        flash("Profile updated!")
        return redirect(url_for('auth.my_account'))


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


@login_required
@bp.route('/base.html', methods=('GET', 'POST'))
def steps_calculator(sex, current_weight, target_weight, body_comp):
    if request.method == 'GET':
        # Get handle on DB
        database = get_database()
        # Get info from the database ???
        sex = "Select sex FROM user where sex = ?".format(sex)
        current_weight = "Select current_weight FROM user where current_weight = ?".format(current_weight)
        target_weight = "Select target_weight FROM user where current_weight = ?".format(target_weight)
        body_comp = "Select target_weight FROM user where current_weight = ?".format(body_comp)
        # calculates the target weight loss
        target_weight_loss = (current_weight - target_weight) / 2.205
        # converts current weight lbs to kgs
        current_weight = current_weight / 2.205
        #target weight in kg
        target_weight_kg = current_weight - target_weight_loss
        # calculates the current fat mass
        current_fatmass = (body_comp * 0.01) * current_weight
        current_fatfree_mass = current_weight - current_fatmass
        new_fat_mass = current_fatmass - target_weight_loss
        target_bodyfat = (new_fat_mass / target_weight_kg) * 100

        if sex == 'Female':
            power_regression = 261425.4 / (target_bodyfat ** 1.8797)
            daily_steps = power_regression * current_fatmass
        else:
            power_regression = 39377.34 / (target_bodyfat ** 1.3405)
            daily_steps = power_regression * current_fatmass

    #adds value to the database ???
    database.execute("INSERT INTO user (steps) VALUES (%s)" % (daily_steps))
    database.commit()

    #displays the value to the page ????
    display = database.execute('SELECT steps FROM user').fetchall()

    return render_template('auth/base.html', display=sex)
