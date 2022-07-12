from flask import Flask, render_template, g, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
import os


app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, "postgres_db_cur"):
        g.postgres_db_cur.close()
    if hasattr(g, "postgres_db_conn"):
        g.postgres_db_conn.close()


def get_current_user():
    user_result = None
    if "user" in session:
        user = session["user"]
        db = get_db()
        db.execute(
            "select id, name,password,admin,expert from users where name = %s", (user,)
        )
        user_result = db.fetchone()
        return user_result


@app.route("/")
def index():
    # user = None
    # if "user" in session:
    #     user = session["user"]
    user = get_current_user()
    db = get_db()
    db.execute(
        """select questions.id as question_id,questions.question_text,askers.name as asker_name,experts.name as expert_name
    from questions join users as askers on askers.id = questions.asked_by_id join users as experts
    on experts.id = questions.expert_id where questions.answer is not null"""
    )
    questions_result = db.fetchall()

    return render_template("home.html", user=user, questions=questions_result)


@app.route("/register", methods={"POST", "GET"})
def register():
    user = get_current_user()
    if request.method == "POST":
        db = get_db()
        db.execute("select id from users where name = %s", (request.form["name"],))
        existing_user = db.fetchone()
        if existing_user:
            return render_template(
                "register.html", user=user, error="User already Exist"
            )
        hashed_password = generate_password_hash(
            request.form["password"], method="sha256"
        )

        db.execute(
            "insert into users (name,password,expert,admin) values(%s,%s,%s,%s)",
            (
                request.form["name"],
                hashed_password,
                "0",
                "0",
            ),
        )

        session["user"] = request.form["name"]
        return redirect(url_for("index"))

    return render_template("register.html", user=user)


@app.route("/login", methods=["POST", "GET"])
def login():
    error = None
    user = get_current_user()
    if request.method == "POST":
        db = get_db()
        name = request.form["name"]
        password = request.form["password"]
        db.execute("select id, name,password from users where name = %s", (name,))
        user_result = db.fetchone()
        if user_result:

            if check_password_hash(user_result["password"], password):
                session["user"] = user_result["name"]
                return redirect(url_for("index"))

            error = "The password is incorrect"

        else:
            error = "The Username is incorrect"

    return render_template("login.html", user=user, error=error)


@app.route("/question/<question_id>")
def question(question_id):
    user = get_current_user()
    db = get_db()
    question_cur = db.execute(
        """select questions.question_text,questions.answer,askers.name as asker_name,experts.name as expert_name 
        from questions join users as askers on 
        askers.id = questions.asked_by_id join users as experts 
        on experts.id = questions.expert_id where questions.id = %s""",
        (question_id,),
    )
    my_question = question_cur.fetchone()
    return render_template("question.html", user=user, question=my_question)


@app.route("/answer/<question_id>", methods=["GET", "POST"])
def answer(question_id):
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    if user.expert == 0:
        return redirect(url_for("index"))
    db = get_db()
    if request.method == "POST":
        db.execute(
            "update questions set answer = %s where id = %s",
            (request.form["answer"], question_id),
        )
        db.commit()
        return redirect(url_for("unanswered"))

    question_cur = db.execute(
        "select id,question_text from questions where id = %s", (question_id,)
    )
    my_question = question_cur.fetchone()
    return render_template("answer.html", user=user, question=my_question)


@app.route("/ask", methods=["GET", "POST"])
def ask():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    db = get_db()
    if request.method == "POST":
        db.execute(
            "insert into questions (question_text,asked_by_id,expert_id) values (%s,%s,%s)",
            (
                request.form["question"],
                user.id,
                request.form["expert"],
            ),
        )
        db.commit()
        return redirect(url_for("index"))

    expert_cur = db.execute("select id,name from users where expert == 1")
    expert_results = expert_cur.fetchall()
    return render_template("ask.html", user=user, experts=expert_results)


@app.route("/unanswered")
def unanswered():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    if user.expert == 0:
        return redirect(url_for("index"))
    db = get_db()
    questions_cur = db.execute(
        """select users.name,
                            questions.id ,
                            questions.question_text from questions
                            join users on users.id = questions.asked_by_id where answer is null and expert_id = %s""",
        (user.id),
    )
    questions = questions_cur.fetchall()
    return render_template("unanswered.html", user=user, questions=questions)


@app.route("/users")
def users():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    if user.admin == 0:
        return redirect(url_for("index"))

    db = get_db()
    users_cur = db.execute("SELECT id,name,expert,admin FROM users")
    users_results = users_cur.fetchall()
    return render_template("users.html", user=user, users=users_results)


@app.route("/promote/<int:user_id>")
def promote(user_id):
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    if user.admin == 0:
        return redirect(url_for("index"))
    db = get_db()
    db.execute("update users set expert = 1 where id= %s", (user_id,))
    db.commit()
    return redirect(url_for("users"))


@app.route("/logout")
def logout():

    session.pop("user", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
