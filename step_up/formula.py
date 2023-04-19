from step_up.database import get_database


def steps_calculator(userid):
    # Get handle on DB
    database = get_database()
    # Get info from the database
    user_info = database.execute(
        "SELECT sex, current_weight, target_weight, body_fat_per FROM user WHERE userid = ?", (userid,)
    ).fetchone()

    sex = user_info['sex']
    current_weight = user_info['current_weight']
    target_weight = user_info['target_weight']
    body_fat_per = user_info['body_fat_per']

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
        "UPDATE user SET steps = ? WHERE userid = ?", (daily_steps, userid))
    database.commit()


def get_steps(userid):
    # Get a handle on the db
    database = get_database()

    # Get current steps
    step = database.execute(
        "Select steps FROM user where userid = ?", (userid,)
    ).fetchone()

    steps = int(step['steps'])

    # if steps == 0:
    #    steps = "Click on 'Survey' to calculate your steps!"

    return steps


def get_user(userid):
    database = get_database()
    user = database.execute(
        "Select * FROM user where userid = ?", (userid,)
    ).fetchone()
    return user
