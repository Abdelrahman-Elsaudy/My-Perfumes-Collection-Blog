from datetime import date
import flask
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
import hashlib
from urllib.parse import urlencode
import datetime
import smtplib
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("APPCONFIGBLOG")
ckeditor = CKEditor(app)
Bootstrap5(app)

today = datetime.datetime.today()
current_year = today.year
my_email = "abdelrahmanelsaudyyy@gmail.com"
password = os.getenv("elsaudyyy_email_pass")


# TODO: Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI")
db = SQLAlchemy(model_class=Base)
db.init_app(app)


gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


# CONFIGURE TABLES
# TODO: Create a User table for all your registered users.
class User(db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False)
    password: Mapped[str] = mapped_column(String(50), nullable=False)
    img_url: Mapped[str] = mapped_column(String)
    is_active = True
    is_authenticated = True
    # Relation with BlogPost to make a list of posts (the children) related to the user (the parent).
    posts: Mapped[list["BlogPost"]] = relationship(back_populates="parent_author")
    comments: Mapped[list["Comments"]] = relationship(back_populates="parent_author")

    def get_id(self):
        return f"{self.id}"


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    # Relation to the user (parent) and using they key to indicate him, users is the name of the User class table.
    parent_author: Mapped["User"] = relationship(back_populates="posts")
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    comments: Mapped[list["Comments"]] = relationship(back_populates="parent_post")


class Comments(db.Model):
    __tablename__ = "commens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    parent_img_url: Mapped[str] = mapped_column(String)

    parent_author: Mapped["User"] = relationship(back_populates="comments")
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    parent_post: Mapped["BlogPost"] = relationship(back_populates="comments")
    post_id: Mapped[int] = mapped_column(ForeignKey("blog_posts.id"))


with app.app_context():
    db.create_all()


def admin_only(function):
    @wraps(function)
    def wrapper_function(*args, **kwargs):
        if current_user.get_id() != "1":
            return flask.abort(403)
        return function(*args, **kwargs)
    return wrapper_function


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = User(name=form.name.data,
                        email=form.email.data,
                        img_url=form.img_url.data,
                        password=generate_password_hash(password=form.password.data,
                                                        method='pbkdf2:sha256',
                                                        salt_length=8))
        all_users = db.session.execute(db.select(User).order_by(User.id)).scalars()
        for user in all_users:
            if user.email == new_user.email:
                flash("User already exists")
                return redirect('login')
        db.session.add(new_user)
        db.session.commit()
        return redirect('login')
    return render_template("register.html", the_form=form, the_year=current_year)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        target_user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if target_user is None:
            flash("User not found in the database.")
            return redirect('login')
        else:
            if check_password_hash(target_user.password, form.password.data):
                login_user(target_user)
                return redirect(url_for('get_all_posts'))
            else:
                flash("Wrong Password.")
                return redirect('login')
    return render_template("login.html", the_form=form, the_year=current_year)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts,
                           logged_in=current_user.is_authenticated, user_id=current_user.get_id(),
                           the_year=current_year)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    form = CommentForm()
    requested_post = db.get_or_404(BlogPost, post_id)
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('You should log in first')
            return redirect(url_for('login'))
        else:
            email_hash = hashlib.sha256(current_user.email.lower().encode('utf-8')).hexdigest()
            query_params = urlencode({'d': current_user.img_url, 's': str(40)})
            gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?{query_params}"
            new_comment = Comments(
                body=form.comment_body.data,
                parent_img_url=gravatar_url,
                parent_author=current_user,
                date=date.today().strftime("%B %d, %Y"),
                parent_post=requested_post
            )
            db.session.add(new_comment)
            db.session.commit()
    all_comments = Comments.query.all()
    return render_template("post.html", post=requested_post, the_form=form,
                           logged_in=current_user.is_authenticated, user_id=current_user.get_id(),
                           comments=all_comments, the_year=current_year)


# TODO: Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            parent_author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form,
                           logged_in=current_user.is_authenticated, the_year=current_year)


# TODO: Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form,
                           is_edit=True, logged_in=current_user.is_authenticated, the_year=current_year)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html", logged_in=current_user.is_authenticated,
                           the_year=current_year)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        msg = f"Name: {request.form['name']}\nEmail: {request.form['email']}\nPhone: {request.form['phone']}\nMessage: {request.form['message']}"
        with smtplib.SMTP("smtp.gmail.com", 587) as connection:
            full_msg = f"Subject: New Connection From Perfumes Blog\n\n{msg}"
            connection.starttls()
            connection.login(user=my_email, password=password)
            connection.sendmail(from_addr=my_email,
                                to_addrs="abdelrahman.elsaudy@gmail.com",
                                msg=full_msg)
            flash('Message sent successfully.')
            return redirect(url_for('get_all_posts'))
    return render_template("contact.html", logged_in=current_user.is_authenticated,
                           the_year=current_year)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5432)
