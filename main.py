from flask import Flask, render_template
from post import Post
import requests

posts = requests.get("https://api.npoint.io/844f6145da7090ef192e").json() # Dummy Blogs
post_objects = [Post(post["id"], post["title"], post["subtitle"], post["body"], post["author"], post["posted_on"], post["image_url"]) for post in posts]

app = Flask(__name__)
@app.route("/")
def home():
    return render_template("index.html", posts=post_objects)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/post/<int:index>")
def show_post(index):
    requested_post = None
    for post in post_objects:
        if post.id == index:
            requested_post = post
    return render_template("post.html", post=requested_post)

if __name__ == "__main__":
    app.run(debug=True)