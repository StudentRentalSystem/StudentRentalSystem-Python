from flask import Flask, render_template, request, redirect, session, jsonify
from src.frontend.embedding_database import EmbeddingDatabase
from src.frontend.user_service import UserService

app = Flask(__name__)
app.secret_key = "super-secret-key"

user_service = UserService()
embedding_database = EmbeddingDatabase()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        name = request.form["name"]
        user = user_service.get_or_create_user(email, name)

        session["user"] = {
            "email": user["email"],
            "name": user["name"]
        }
        return redirect("/search")

    return render_template("login.html")
@app.route("/search", methods=["GET", "POST"])
def search():
    if "user" not in session:
        return redirect("/")

    results = session.get('last_results', [])
    if request.method == "POST":
        keyword = request.form["keyword"]
        email = session["user"]["email"]

        user_service.add_history(email, keyword)
        results = embedding_database.search_rentals(keyword)
        session['last_results'] = results

    collections = user_service.get_collections(session["user"]["email"])

    return render_template(
        "index.html",
        results=results,
        collections=collections,
    )


@app.route("/toggle-collection", methods=["POST"])
def toggle_collection():
    if "user" not in session:
        return jsonify({"error": "unauthorized"}), 401

    data = request.json
    post_id = str(data["post_id"])
    email = session["user"]["email"]

    collections = user_service.get_collections(email)

    if post_id in collections:
        user_service.remove_collection(email, post_id)
        return jsonify({"status": "removed"})
    else:
        user_service.add_collection(email, post_id)
        return jsonify({"status": "added"})


@app.route("/collection")
def collection():
    if "user" not in session:
        return redirect("/")

    email = session["user"]["email"]
    ids = user_service.get_collections(email)

    posts = embedding_database.get_rental_info_by_ids(ids)

    return render_template("collection.html", posts=posts)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/")
    email = session["user"]["email"]
    hist = user_service.get_history(email)
    return render_template("history.html", history=hist)

@app.route('/clean_history', methods=['GET'])
def clean_history():
    if "user" not in session:
        return redirect("/")
    email = session["user"]["email"]
    user_service.clean_history(email)
    return redirect('history')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')