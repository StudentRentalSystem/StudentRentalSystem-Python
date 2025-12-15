from flask import Flask, render_template, request, redirect, session, jsonify
from embedding_database import search_rentals, get_rental_info_by_ids
from user_service import UserService
from llm_service import LLMService

app = Flask(__name__)
app.secret_key = "super-secret-key"

user_service = UserService()
llm_service = LLMService()

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

    results = []
    query_json = session.get('last_query')

    if request.method == "POST":
        keyword = request.form["keyword"]
        email = session["user"]["email"]

        user_service.add_history(email, keyword)

        query_json = llm_service.generate_mongo_query(keyword)

        results = search_rentals(query_json)

        session['last_query'] = query_json
        session['last_keyword'] = keyword

    if query_json:
        results = search_rentals(query_json)

    collections = user_service.get_collections(session["user"]["email"])

    return render_template(
        "index.html",
        results=results,
        collections=collections,
        query=query_json,
        keyword=session.get("last_keyword", "")
    )

@app.route("/toggle-collection", methods=["POST"])
def toggle_collection():
    data = request.json
    post_id = data["post_id"]
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
    email = session["user"]["email"]
    ids = user_service.get_collections(email)
    posts = get_rental_info_by_ids(ids)
    return render_template("collection.html", posts=posts)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/history")
def history():
    email = session["user"]["email"]
    history = user_service.get_history(email)
    return render_template("history.html", history=history)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')