# CS50 Golf Index
> * model: sql sqlite3
> * view: html css bootstrap javascript
> * controller: python flask

#### GitHub: Flandersfrybad
#### Youtube: https://youtu.be/33wfsSF3XYY?si=nw8JATXGJp8AGkej

>### Golf Index stores golf courses, scores, and calculates the average index differential.

***

#### User experience work flow:
1. Register username and password (twice).
2. Login with username and password.
3. Average index differential from recent 20 or less scores.
    * Edit score
    * Delete score
4. Add course for differential calculation.
5. Add Score calculates/adds score.
6. History of all scores including inactive.
    * Edit score
    * Toggle active/inactive
7. Change Password
8. Logout

***

### Handicap Index Calculation

A Score Differential measures the performance of a round in relation to the relative difficulty of the course that was played, measured by the Course Rating™ and Slope Rating™ .

# Differential = (113 / Slope) x (Adjusted Gross Score - Rating)

layout.html serves as a consistent template for the web app structure including the navigation bar, css and bootstrap styling.

![image](static/I_heart_validator.png)

## Users

Registration requires two matching passwords; must have at least 1 letter, 1 number, 1 symbol, and 8 characters.
```
    <form action="/register" method="post">
        <div class="mb-3">
            <input name="username" placeholder="Username" type="text">
        </div>
        <button class="btn btn-primary" type="submit">Register</button>
    </form>
```
```
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # username and password checked and stored
        return redirect("/login")
    return render_template("register.html")
```
Username, Password(hash), and Average Index Differential (Handicap) is stored in Table Users.
>## users
>|id|username|hash|aid|
>|---|---|---|---|
>|1|james|scrypt:32768:8:1$KDfe|3.6|


login.html is the default starting page
```
<form action="/login" method="post">
    <div class="mb-3">
        <input autocomplete="off" name="username" placeholder="Username" type="text">
    </div>
    <button class="btn btn-primary" type="submit">Log In</button>
</form>
```
```
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear() # Forget any user_id
    if request.method == "POST":
        # if username and password match database.
        return redirect("/")
    return render_template("login.html")
```
## Courses

A course must exist in Table Courses in order to calculate the Score Differential.

>### courses
>|id|course|
>|---|---|
>|1|Collindale|
>|2|Southridge|
>|---|---|
layout.html navigation bar.
```
<li class="nav-item"><a class="nav-link" href="/courses">Courses</a></li>
```
The course is typed in.
```
<form action="/courses" method="post">
    <div class="mb-3">
        <label for="course">Course</label>
        <input id="course" type="text" name="course" value="Collindale">
    </div>
</form>
```

## Tees

```
@app.route("/courses", methods=["GET", "POST"])
@login_required  # <- def login_required(f):
def courses():
    if request.method == "POST":
    # if course tee combination not in database insert all input.
        flash('Course added!')
    else:
        flash("This course tee combination already exists.")
    return redirect("/courses")
```
One course will have multiple tees (red, white, blue) and corresponding Rating and Slope in Table Tees.
>## tees
>|id|course_id|tee|rating|slope|
>|---|---|---|---|---|
>|1|1|White|69.3|130|
>|2|1|Blue|70.9|134|
>|---|---|---|---|---|

The color, rating, and slope are typed in. This could be a scraper or api driven by course and tee returning rating and slope.
```
{% for course in courses %}
    {% for tee in tees %}
        {% if tee.course_id == course.id %}
            <tr>
                <td class="text-center">{{ course.course }}</td>
                <td class="text-center">{{ tee.tee }}</td>
                <td class="text-center">{{ tee.rating }}</td>
                <td class="text-center">{{ tee.slope }}</td>
            </tr>
        {% endif %}
    {% endfor %}
{% endfor %}
```
courses.html displays course, tee, rating, and slope.
## Scores

User, course, tee, score, rating, slope, calculated differential, date time posted, and active are in Table Scores.

>## scores
>|id|user_id|course|tee|score|rating|slope|diff|posted|active|
>|---|---|---|---|---|---|---|---|---|---|
>|1|1|Collindale|White|75|69.3|130|5|2025-02-01 15:25:08|1|
>|2|1|Collindale|Blue|74|69.3|130|4.1|2025-02-01 15:27:31|1|
>|---|---|---|---|---|---|---|---|---|---|

add.html dynamically offers courses in a dropdown menu from Table Courses. Tee dropdown is dynamically driven from only tees that match course_id in Table Tees. Rating and slope prepopulate and differential is calculated for submittal to Table Scores.
```
<form action="/add" method="post">
    <div class="mb-3">
        <label for="course">Course</label>
        <input type="hidden" name="course">
        <select id="course" name="course">
            <option value="" disabled selected>Select a course</option>
            {% for course in courses %}
                <option value={{ course.id }}>{{ course.course }}</option>
            {% endfor %}
        </select>
    </div>
```
```
@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    user_id = session.get("user_id")
    if request.method == "POST":
        # Insert course, tee, score, rating, slope, and differential into Table Scores
        flash('Round added!')
        return redirect("/")

    courses = db.execute("SELECT * FROM courses") # "GET" loads options
    tees = db.execute("SELECT * FROM tees")
    return render_template("add.html", courses=courses, tees=tees)
```
## "/"

"/" is the default resting page and renders index.html.
>## index
>|Course|Tee|Score|Rating|Slope|Differential|Edit|Delete|Date Posted|
>|---|---|---|---|---|---|---|---|---|
>|Collindale|White|75|69.3|130|5|Edit|Delete|2025-02-01 15:25:08|
>|Collindale|Blue|74|69.3|130|4.1|Edit|Delete|2025-02-01 15:27:31|
>|---|---|---|---|---|---|---|---|---|

Edit 'get' feeds edit.html, 'post' feeds '/' (index).
```
<form action="/edit" method="post">
    <div class="mb-3">
        <input type="hidden" name="id" value="{{ id }}">
    </div>
```
```
@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "POST":
        # Construct the SQL UPDATE statement
        db.execute("UPDATE scores SET course = ?, tee = ?, score = ?, rating = ?, slope = ?, diff = ? WHERE id = ?", course, tee, score, rating, slope, diff, id)
        flash('Round edited!')
        return redirect("/")

    return render_template("edit.html", id=id, course=course, tee=tee, score=score, rating=rating, slope=slope, diff=diff)
```

Delete toggles active column in Table Scores. Rubber Duck Debugger helped write most the javascript code.
