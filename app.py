from flask import Flask, render_template, g, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
import os


app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, "sqlite_db"):
        g.sqlite_db.close()


@app.route("/")
def index():
    # user = None
    # if "user" in session:
    #     user = session["user"]
    user = get_current_user()

    return render_template("home.html", user=user)


def get_current_user():
    user_result = None
    if "user" in session:
        user = session["user"]
        db = get_db()
        user_cur = db.execute(
            "select id, name,password,admin,expert from users where name = ?", [user]
        )
        user_result = user_cur.fetchone()
        return user_result


@app.route("/register", methods={"POST", "GET"})
def register():
    user = get_current_user()
    if request.method == "POST":
        db = get_db()
        hashed_password = generate_password_hash(
            request.form["password"], method="sha256"
        )
        db.execute(
            "insert into users (name,password,expert,admin) values(?,?,?,?)",
            [
                request.form["name"],
                hashed_password,
                0,
                0,
            ],
        )
        db.commit()
        session["user"] = request.form["name"]
        return redirect(url_for("index"))

    return render_template("register.html", user=user)


@app.route("/login", methods=["POST", "GET"])
def login():
    user = get_current_user()
    if request.method == "POST":
        db = get_db()
        name = request.form["name"]
        password = request.form["password"]
        user_cur = db.execute(
            "select id, name,password from users where name = ?", [name]
        )
        user_result = user_cur.fetchone()
        if check_password_hash(user_result["password"], password):
            session["user"] = user_result["name"]
            return redirect(url_for("index"))
        else:
            return "<h1>The password is incorrect</h1>"

    return render_template("login.html", user=user)


@app.route("/question")
def question():
    user = get_current_user()
    return render_template("question.html", user=user)


@app.route("/answer")
def answer():
    user = get_current_user()
    return render_template("answer.html", user=user)


@app.route("/ask", methods=["GET", "POST"])
def ask():
    if request.method == "POST":
        return f"Question: {request.form['question']}, Expert ID: {request.form['expert']} "
    user = get_current_user()
    db = get_db()
    expert_cur = db.execute("select id,name from users where expert == 1")
    expert_results = expert_cur.fetchall()
    return render_template("ask.html", user=user, experts=expert_results)


@app.route("/unanswered")
def unanswered():
    user = get_current_user()
    return render_template("unanswered.html", user=user)


@app.route("/users")
def users():
    user = get_current_user()

    db = get_db()
    users_cur = db.execute("SELECT id,name,expert,admin FROM users")
    users_results = users_cur.fetchall()
    return render_template("users.html", user=user, users=users_results)


@app.route("/promote/<int:user_id>")
def promote(user_id):
    db = get_db()
    db.execute("update users set expert = 1 where id= ?", [user_id])
    db.commit()
    return redirect(url_for("users"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
