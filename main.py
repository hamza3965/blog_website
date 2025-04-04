from flask import Flask, render_template, request
from post import Post
import smtplib
import os
from dotenv import load_dotenv
import requests

load_dotenv()
MY_EMAIL = os.getenv("EMAIL") # Your Email
MY_PASSWORD = os.getenv("PASSWORD") # Your App Password from Google (16 characters long string with no spaces)

posts = requests.get("https://api.npoint.io/844f6145da7090ef192e").json() # Dummy Blogs
post_objects = [Post(post["id"], post["title"], post["subtitle"], post["body"], post["author"], post["posted_on"], post["image_url"]) for post in posts]

app = Flask(__name__)
@app.route("/")
def home():
    return render_template("index.html", posts=post_objects)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        message = request.form["message"]
        email_body = (
            f"Subject: 📧 New message from {name}\n"
            f"Content-Type: text/plain; charset=utf-8\n\n"
            f"Name: {name}\n\n"
            f"Email: {email}\n\n"
            f"Phone: {phone}\n\n"
            f"Message: {message}\n\n"
            f"this message comes from your blog website. "
            f"Best,\nYour Blog Team"
        )

        with smtplib.SMTP("smtp.gmail.com") as connection: # Replace with your email provider
            connection.starttls()
            connection.login(MY_EMAIL, MY_PASSWORD)
            connection.sendmail(from_addr=MY_EMAIL, to_addrs=MY_EMAIL, msg=email_body.encode("utf-8"))
        return render_template("contact.html", msg_sent=True)
    
    return render_template("contact.html", msg_sent=False)

@app.route("/post/<int:index>")
def show_post(index):
    requested_post = None
    for post in post_objects:
        if post.id == index:
            requested_post = post
    return render_template("post.html", post=requested_post)

if __name__ == "__main__":
    app.run(debug=True)