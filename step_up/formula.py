from step_up.database import get_mysql
from step_up.__init__ import mysql


def steps_calculator(userid):
    # Get handle on DB
    conn = mysql.connect()
    database = conn.cursor()
    # Get info from the database
    database.execute(
        "SELECT * FROM user WHERE userid = %s", (userid,)
    )
    user_info = database.fetchone()

    sex = user_info[5]
    current_weight = user_info[10]
    target_weight = user_info[11]
    body_fat_per = user_info[14]

    # conversion for kilograms from pounds: '/ 2.205'
    current_weight_kg = current_weight / 2.205
    # calculates the current fat mass (30?)
    current_fat_mass = (body_fat_per * 0.01) * current_weight_kg
    # converts the target weight loss into decimal (7.2?)
    target_weight_loss = current_weight_kg * (target_weight * .01)
    # target weight in kg
    target_body_weight = current_weight_kg - target_weight_loss
    # temporary new fat mass
    new_fat_mass = current_fat_mass - target_weight_loss
    # target body fat percentage
    target_body_fat = (new_fat_mass / target_body_weight) * 100
    # Holding for later... current_fat_free_mass = current_weight_kg - current_fat_mass

    if sex == 'female':
        power_regression = 261425.4 / (target_body_fat ** 1.8797)
        daily_steps = power_regression * current_fat_mass
    else:
        power_regression = 39377.34 / (target_body_fat ** 1.3405)
        daily_steps = power_regression * current_fat_mass

    int(daily_steps)

    # Adds value to the database
    database.execute(
        "UPDATE user SET steps = %s WHERE userid = %s", (daily_steps, userid))
    conn.commit()


def get_steps(userid):
    # Get a handle on the db
    database = get_mysql()

    # Get current steps
    database.execute(
        "Select steps FROM user where userid = %s", (userid,)
    )
    step = database.fetchone()

    steps = int(step[0])

    # if steps == 0:
    #    steps = "Click on 'Survey' to calculate your steps!"

    return steps


def get_user(userid):
    database = get_mysql()
    database.execute(
        "Select * FROM user where userid = %s", (userid,)
    )
    user = database.fetchone()
    return user
