import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
# from werkzeug.security import check_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///golf.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show previous 20 or less scores"""

    user_id = session.get("user_id")
    scores = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='scores'")
    if not scores: return apology("Welcome to the jungle. No scores added yet.")
    else:
        rows = db.execute("SELECT id, course, tee, score, rating, slope, diff, posted FROM scores WHERE user_id = ? AND active ORDER BY posted DESC", user_id)
        for i in range(min(20, len(rows))):
            current = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='current'")
            if not current:
                db.execute("CREATE TABLE current (id INTEGER, user_id INTEGER, course TEXT, tee TEXT, score INTEGER, rating DECIMAL(3, 1), slope INTEGER, diff DECIMAL(3, 1), posted DATETIME)")
            db.execute("INSERT INTO current (id, user_id, course, tee, score, rating, slope, diff, posted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows[i]['id'], user_id, rows[i]['course'], rows[i]['tee'], rows[i]['score'], rows[i]['rating'], rows[i]['slope'], rows[i]['diff'], rows[i]['posted'])

    current = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='current'")
    if current:
        rows = db.execute("SELECT * FROM current WHERE user_id = ?", user_id)

        scorelist = [row['diff'] for row in rows]
        sorted_scores = sorted(scorelist)
        num_scores = len(scorelist)

        # Define the mapping
        mapping = {
            range(19, 21): num_scores - 12,
            range(17, 19): 6,
            range(15, 17): 5,
            range(12, 15): 4,
            range(9, 12): 3,
            range(7, 9): 2,
            range(6, 7): 2,
            range(5, 6): 1,
            range(4, 5): 1,
            range(3, 4): 1
        }

        # Determine the number of lowest scores to average
        for key, value in mapping.items():
            if num_scores in key:
                selected_scores = sorted_scores[:value]
                break

        # Adjustments for specific cases
        two = False
        if num_scores == 6:
            average = sum(selected_scores) / len(selected_scores) - 1
        elif num_scores == 4:
            average = min(selected_scores) - 1
        elif num_scores == 3:
            average = min(selected_scores) - 2
        elif num_scores < 3:
            two = True
        else:
            average = sum(selected_scores) / len(selected_scores)

        db.execute("DROP TABLE current")
        flash('Welcome Home!')
        if two: average = "Atleast 3 scores required to calculate your average differential."
        else: average = round(average, 1)

        # Update average in users tp prepopulate /add
        db.execute("UPDATE users SET aid = ? WHERE id = ?", average, user_id)

        return render_template("index.html", rows=rows, average=average)

    flash('Welcome Home! No scores entered yet!')
    return render_template("index.html")


@app.route("/courses", methods=["GET", "POST"])
@login_required
def courses():
    """select course"""

    if request.method == "POST":
        course = request.form.get("course")
        tee = request.form.get("tee")
        rating = request.form.get("rating")
        slope = request.form.get("slope")

        if not course:return apology("must provide course")
        if not tee:return apology("must provide tee")
        if not rating: return apology("must provide course rating")
        if not slope: return apology("must provide course slope")

        # Check if courses table exists, if not, create it
        courses = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='courses'")
        if not courses:
            db.execute("CREATE TABLE courses (id INTEGER PRIMARY KEY, course TEXT UNIQUE)")

        # Check if tees table exists, if not, create it
        tees = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tees'")
        if not tees:
            db.execute("CREATE TABLE tees (id INTEGER PRIMARY KEY, course_id INTEGER, tee TEXT, rating DECIMAL(3, 1), slope INTEGER, UNIQUE(course_id, tee), FOREIGN KEY(course_id) REFERENCES courses(id))")

        # Check if the course already exists
        existing_course = db.execute("SELECT id FROM courses WHERE course = ?", course)
        if not existing_course:
            db.execute("INSERT INTO courses (course) VALUES (?)", course)
            course_id = db.execute("SELECT id FROM courses WHERE course = ?", course)[0]['id']
        else:
            course_id = existing_course[0]['id']

        # Check if course-tee combination already exists
        existing_tee = db.execute("SELECT id FROM tees WHERE course_id = ? AND tee = ?", course_id, tee)
        if not existing_tee:
            db.execute("INSERT INTO tees (course_id, tee, rating, slope) VALUES (?, ?, ?, ?)", course_id, tee, rating, slope)
            flash('Course added!')
        else:
            flash("This course tee combination already exists.")

        return redirect("/courses")


    # Check if courses table exists, if not, create it
    courses = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='courses'")
    if not courses:
        db.execute("CREATE TABLE courses (id INTEGER PRIMARY KEY, course TEXT UNIQUE)")

    # Check if tees table exists, if not, create it
    tees = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tees'")
    if not tees:
        db.execute("CREATE TABLE tees (id INTEGER PRIMARY KEY, course_id INTEGER, tee TEXT, rating DECIMAL(3, 1), slope INTEGER, UNIQUE(course_id, tee), FOREIGN KEY(course_id) REFERENCES courses(id))")

    # Query the tables
    courses = db.execute("SELECT * FROM courses")
    tees = db.execute("SELECT * FROM tees")

    return render_template("courses.html", courses=courses, tees=tees)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """add score"""

    user_id = session.get("user_id")

    if request.method == "POST":
        course = request.form.get("course")
        tee = request.form.get("tee")
        print('tee', tee)
        score = request.form.get("score")
        rating = request.form.get("rating")
        slope = request.form.get("slope")
        diff = request.form.get("differential")

        if not course:return apology("must provide course")
        if not tee:return apology("must provide tee")
        if not score:return apology("must provide score")
        if not rating: return apology("must provide course rating")
        if not slope: return apology("must provide course slope")
        if not diff: return apology("must provide differential")

        scores = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scores'")
        if not scores:
            db.execute("CREATE TABLE scores (id INTEGER PRIMARY KEY, user_id INTEGER, course TEXT, tee TEXT, score INTEGER, rating DECIMAL(3, 1), slope INTEGER, diff DECIMAL(3, 1), posted DATETIME, active BOOLEAN)")

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print('wow', tee)
        db.execute("INSERT INTO scores (user_id, course, tee, score, rating, slope, diff, posted, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   user_id, course, tee, score, rating, slope, diff, current_time, 1)

        flash('Round added!')
        return redirect("/")

    courses = db.execute("SELECT * FROM courses")
    tees = db.execute("SELECT * FROM tees")
    print(tees)
    print(courses)
    return render_template("add.html", courses=courses, tees=tees)


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    """edit score"""

    if request.method == "POST":
        id = request.form.get("id")
        course = request.form.get("course")
        tee = request.form.get("tee")
        score = request.form.get("score")
        rating = request.form.get("rating")
        slope = request.form.get("slope")
        diff = request.form.get("differential")

        if not id: return apology("must provide id")
        if not course: return apology("must provide course")
        if not tee: return apology("must provide tee")
        if not score: return apology("must provide score")
        if not rating: return apology("must provide rating")
        if not slope: return apology("must provide slope")
        if not diff: return apology("must provide diff")

        # Construct the SQL UPDATE statement
        db.execute("UPDATE scores SET course = ?, tee = ?, score = ?, rating = ?, slope = ?, diff = ? WHERE id = ?", course, tee, score, rating, slope, diff, id)

        flash('Round edited!')
        return redirect("/")

    id = request.args.get("id")
    course = request.args.get("course")
    tee = request.args.get("tee")
    score = request.args.get("score")
    rating = request.args.get("rating")
    slope = request.args.get("slope")
    diff = request.args.get("diff")

    if not id: return apology("must provide id")
    if not course: return apology("must provide course")
    if not tee: return apology("must provide tee")
    if not score: return apology("must provide score")
    if not rating: return apology("must provide rating")
    if not slope: return apology("must provide slope")
    if not diff: return apology("must provide diff")

    return render_template("edit.html", id=id, course=course, tee=tee, score=score, rating=rating, slope=slope, diff=diff)

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Get rows of score into current
    user_id = session.get("user_id")
    scores = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='scores'")
    if not scores: return apology("No scores added yet, so you got that going for ya, which is nice.")
    else:
        rows = db.execute("SELECT id, course, tee, score, rating, slope, diff, posted, active FROM scores WHERE user_id = ? ORDER BY posted DESC", user_id)
        for row in rows:
            current = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='current'")
            if not current:
                db.execute("CREATE TABLE current (id INTEGER, user_id INTEGER, course TEXT, tee TEXT, score INTEGER, rating DECIMAL, slope INTEGER, diff DECIMAL, posted DATETIME, active BOOLEAN)")
            db.execute("INSERT INTO current (id, user_id, course, tee, score, rating, slope, diff, posted, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", row['id'], user_id, row['course'], row['tee'], row['score'], row['rating'], row['slope'], row['diff'], row['posted'], row['active'])

    # Send current rows to history.html
    current = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='current'")
    if current:
        rows = db.execute("SELECT * FROM current WHERE user_id = ?", user_id)

        db.execute("DROP TABLE current")
        flash('All the laps!')
        return render_template("history.html", rows=rows)

    flash('No laps yet!')
    return render_template("history.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted # return apology("TODO")
        username = request.form.get("username")
        if not username:
            return apology("must provide username")
        name = db.execute("SELECT username FROM users WHERE username = ?", username)
        if name:
            return apology("username already exists")

        password = request.form.get("password")
        alpha = num = sym = length = False
        if len(password) >= 8:
            length = True
        for char in password:
            if not alpha and char.isalpha():
                alpha = True
            if not num and char.isdigit():
                num = True
            if not sym and not char.isalnum():
                sym = True

        if not alpha or not num or not sym or not length:
            return apology("password must have at least 1 letter, 1 number, 1 symbol, and be 8 characters long")

        confirmation = request.form.get("confirmation")
        if not password or not confirmation:
            return apology("must provide passwords")
        if password != confirmation:
            return apology("passwords don't match")

        db.execute("INSERT INTO users (username, hash, aid) VALUES (?, ?, ?)",
                   username, generate_password_hash(password), 0)

        return redirect("/login")

    return render_template("register.html")


@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    """Delete the round, active = 0"""

    user_id = session.get("user_id")

    if request.method == "POST":
        id = request.form.get("id")
        if not id:
            return apology("must have row id", 403)
        scores = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='scores'")
        if not scores:
            return apology("no rounds, empty clip", 403)
        db.execute("UPDATE scores SET active = ? WHERE user_id = ? and id = ?", 0, user_id, id)

        flash('Deleted!')
        return redirect("/")


@app.route("/toggle_status", methods=["GET", "POST"])
@login_required
def toggle_status():
    """Toggle inactive 0 to active 1 and visversa"""

    user_id = session.get("user_id")

    if request.method == "POST":
        data = request.get_json()
        id = data.get("id")
        action = data.get("action")

        if not id:
            return apology("must have row id", 403)
        scores = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='scores'")
        if not scores:
            return apology("no rounds, empty clip", 403)
        if action == "deactivate":
            db.execute("UPDATE scores SET active = ? WHERE user_id = ? and id = ?", 0, user_id, id)
        elif action == "activate":
            db.execute("UPDATE scores SET active = ? WHERE user_id = ? and id = ?", 1, user_id, id)

        return jsonify(success=True, row_class='inactive-row' if action == 'deactivate' else '')


@app.route("/change", methods=["GET", "POST"])
def change():
    """change password"""

    user_id = session.get("user_id")
    if request.method == "POST":
        # Ensure username was submitted # return apology("TODO")
        username = request.form.get("username")
        if not username:
            return apology("must provide username")
        name = db.execute("SELECT username FROM users WHERE username = ?", username)
        if not name:
            return apology("username not in database")
        user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
        user_name = user[0]['username']
        name = name[0]['username']
        if name != user_name:  # input name != logged in name
            return apology("you are not logged in as {} you are logged in as {}".format(name[0]['username'], user_name))

        password = request.form.get("password")
        if not password:
            return apology("must provide current password")

        hash = db.execute("SELECT hash FROM users WHERE id = ?", user_id)
        if check_password_hash(hash[0]['hash'], password):
            print("Password is correct")
        else:
            return apology("incorrect current password")

        new_password = request.form.get("new_password")

        alpha = num = sym = length = False
        if len(new_password) >= 8:
            length = True
        for char in new_password:
            if not alpha and char.isalpha():
                alpha = True
            if not num and char.isdigit():
                num = True
            if not sym and not char.isalnum():
                sym = True

        if not alpha or not num or not sym or not length:
            return apology("new password must have at least 1 letter, 1 number, 1 symbol, and be 8 characters long")

        confirmation = request.form.get("confirmation")
        if not new_password or not confirmation:
            return apology("must provide new password and new password (again)")
        if new_password != confirmation:
            return apology("new password and new password (again) do not match")
        if new_password == password:
            return apology("new password can not match current password")

        db.execute("UPDATE users SET hash = ? WHERE id = ?",
                   generate_password_hash(new_password), user_id)

        flash('Password Changed!')
        return redirect("/")

    return render_template("change.html")

