import functools
import re
from io import BytesIO

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
)
from PIL import Image
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from step_up.database import get_database
from step_up.formula import steps_calculator
from step_up.email import send_approval

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
                    "current_weight, target_weight, weight_circum, neck_circum, body_fat_per, steps, role,"
                    "survey_update) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (username, email, password, 'male', 'other', 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, today)
                )
                # Write the change to the database
                database.commit()
                send_approval(username, email)
                flash('Account Created!')

            # Catch database errors
            except (database.InternalError,
                    database.IntegrityError):
                error = "Unexpected database issue."
            else:
                return render_template('auth/login.html')
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
def patient_survey():
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
        body_fat_per = request.form['body_fat_per']

        # Get a handle on the database and set error value
        database = get_database()
        error = None

        # Validate Data todo(add more validation)
        if not sex:
            error = 'Please enter your sex'
        if not race:
            error = 'Please enter your race'
        if not age:
            error = 'Please enter your date of birth'
        # elif age:
            #     if not isinstance(age, int):
        #         error = 'Your age must be a number'
        if not feet:
            error = 'Please enter your feet in height'
            # elif feet:
            #     if not isinstance(feet, int):
            #         error = 'Your height in feet must be a number'
        if not inches:
            error = 'Please enter your inches in height'
            # elif inches:
            #    if not isinstance(inches, int):
            #        error = 'Your height in inches must be a number'
        if not current_weight:
            error = 'Please enter your current weight in pounds (lb)'
            # elif current_weight:
            #   if not isinstance(current_weight, int):
            #       error = 'Your current weight in pounds (lb) must be a number'
        if not target_weight:
            error = 'Please enter your target weight'
            # elif target_weight:
            #   if not isinstance(target_weight, int):
            #       error = 'Your target weight in kilograms (kg) must be a number'
        if not weight_circum:
            error = 'Please enter your weight circumference'
            # elif weight_circum:
            #  if not isinstance(weight_circum, int):
            #      error = 'Your weight circumference must be a number'
        if not neck_circum:
            error = 'Please enter your neck circumference'
            # elif neck_circum:
            # if not isinstance(neck_circum, int):
            #      error = 'Your neck circumference must be a number'
        if not body_fat_per:
            error = 'Please enter your body composition percent'
            # elif body_fat_per:
            #  if not isinstance(body_fat_per, int):
            #      error = 'Your body fat percentage must be a number'

        if error is None:
            try:
                # Change values in database
                database.execute(
                    "UPDATE user SET sex = ?, race = ?, age = ?, feet = ?, inches = ?,"
                    "current_weight = ?, target_weight = ?, weight_circum = ?, neck_circum = ?, body_fat_per = ? "
                    "WHERE userid = ?",
                    (sex, race, age, feet, inches, current_weight, target_weight, weight_circum, neck_circum,
                     body_fat_per, g.user['userid'])
                )
                database.commit()
                steps_calculator(g.user['userid'])
                # Tell the user it worked
                flash("Info updated!")
            # Catch any errors
            except (database.InternalError,
                    database.IntegrityError):
                error = f"Unable to update survey"
            else:
                return redirect(url_for('mainpage'))
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
                "UPDATE users SET email_address = ?, username = ?, address = ? WHERE userid = ?",
                (email, username, g.user['userid'])
            )
            database.commit()
        # Tell the user it worked
        flash("Profile updated!")
        return redirect(url_for('auth.my_account'))
    return render_template("auth/my_account.html")


@bp.route('/manage_users', methods=('GET',))
@login_required
def manage_info():
    """
    Allows administrators to manage users of the system
    """
    if g.user['role'] == 1:
        user_list = None
        if request.method == 'GET':
            # Get all users from the DB
            database = get_database()
            user_list = database.execute(
                "SELECT * FROM user"
            ).fetchall()
            # Display them on the page
        return render_template('auth/manage_info.html', users=user_list)
    else:
        abort(403)


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


@bp.route('/help_page')
def help_page():
    """
    View the help page selected from the page header
    """

    # Load the help page
    return render_template('auth/help.html')
