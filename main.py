from flask import Flask, render_template, redirect, url_for, request, abort, flash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_gravatar import Gravatar
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from datetime import date
from dotenv import load_dotenv
import smtplib
import os

load_dotenv()
MY_EMAIL = os.getenv("EMAIL") # Your Email
MY_PASSWORD = os.getenv("PASSWORD") # Your App Password from Google (16 characters long string with no spaces)



app = Flask(__name__)
app.secret_key = '8BYkEfBA6O6donzWlSihBXox7C0ssdfsdKR6b'
app.config['CKEDITOR_ENABLE_CODESNIPPET'] = True
app.config['CKEDITOR_PKG_TYPE'] = 'full'
ckeditor = CKEditor(app)
Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CONFIGURE TABLE
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="author")

    def __init__(self, email: str, password: str, name: str):
        self.name = name
        self.email = email
        self.password = password

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")

class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="comments")
    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    text: Mapped[str] = mapped_column(Text, nullable=False)


with app.app_context():
    db.create_all()


# (email:- admin@gmail.com, password:- Admin) 🤫
def admin_only(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if current_user.id == 1:
            return func(*args, **kwargs)
        return abort(403)
    return inner

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

@app.route('/register', methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        name = register_form.name.data
        email = register_form.email.data
        password = register_form.password.data

        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user:
            flash(message="This email’s already in use, Try login instead.", category="info")
            return redirect(url_for('login'))

        hash_and_salted_pass = generate_password_hash(
            password,
            method="pbkdf2:sha256",
            salt_length=8
        )

        new_user = User(name=name, email=email, password=hash_and_salted_pass)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash(f'Welcome {current_user.name}!', "success")
        return redirect(url_for("get_all_posts"))

    return render_template("register.html", form=register_form)


@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if not user or not check_password_hash(user.password, password):
            flash("Invalid Credentials", category="danger")
            return redirect(url_for("login"))
        login_user(user)
        flash(f"Welcome Back {current_user.name}!", category="success")
        return redirect(url_for("get_all_posts"))
    return render_template("login.html", form=login_form)


@app.route('/logout')
@login_required
def logout():
    flash(f"Logged out successfully.", "success")
    logout_user()
    return redirect(url_for('get_all_posts'))

@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)

@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    result = db.session.execute(db.select(Comment))
    all_comments = result.scalars()

    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.", category="info")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=comment_form.comment_text.data,
            author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", post=requested_post, form=comment_form, comments=all_comments)


@app.route("/new-post", methods=["GET", "POST"])
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)

@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)

@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for("get_all_posts"))


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

if __name__ == "__main__":
    app.run(debug=True)