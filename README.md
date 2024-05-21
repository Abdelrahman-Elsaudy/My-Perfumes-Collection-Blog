# My Perfumes Blog

---

- You can check the live version of the blog [here](https://my-perfumes-collection-blog.onrender.com/), it might take a minute to reload.
- You can also check a Youtube video of the blog [here](https://youtu.be/jq0DdgrmISk).
- This blog is a capstone project on _web development_ (frontend and backend).
- It's about my perfumes collection, on which I write blog posts about my experience and opinion on each perfume that I own, 
and users can sign up and comment on these posts.

![homepagegif](https://github.com/Abdelrahman-Elsaudy/Shopping-Price-Alert/assets/158151388/659c34b7-1791-4c5d-bba7-c910c66a8196)

---

## Skills Practiced:

---

- Backend Web Development using `Flask`.
- Frontend Web Development using `HTML` and `CSS`.
- Utilizing `Bootstrap` templates.
- Creating and using `SQLite` and `POSTGRESQL` Databases.
- Hashing passwords using `Werkzeug`.
- Web hosting and deploying on `Render.com`.
- Sending and receiving emails using `SMTP` module.

---

## Features:

---

**1. Interconnected Database**
- A SQLite database that has three tables: users, posts and comments, these tables are related to each other.
```
class User(db.Model):
    __tablename__ = "users"
    posts: Mapped[list["BlogPost"]] = relationship(back_populates="parent_author")
    comments: Mapped[list["Comments"]] = relationship(back_populates="parent_author")
```

**2. Admin Only Features**
- Creating a decorator function to be added to the functions that can add, edit or delete posts.

```
# Creating the decorator function.
def admin_only(function):
    @wraps(function)
    def wrapper_function(*args, **kwargs):
        if current_user.get_id() != "1":
            return flask.abort(403)
        return function(*args, **kwargs)
    return wrapper_function
    
# Adding it to the admin only feature functions.
@app.route("/new-post", methods=["GET", "POST"])
@admin_only
```

**3. Flashing Messages**
- Messages that appear in red for the user, for example: when they try to comment without logging in, or when they 
submit an already existing email in the database.
```
    # Backend:
    all_users = db.session.execute(db.select(User).order_by(User.id)).scalars()
    for user in all_users:
        if user.email == new_user.email:
            flash("User already exists")
            return redirect('login')
    
    # Frontend:
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for message in messages %}
         <p class="flash">{{ message }}</p>
        {% endfor %}
      {% endif %}
    {% endwith %}
```

**4. Flask CKEditor**
- Using the `Flask CKEditor` package to make the blog content (body) and comments into a full CKEditor.
```
    {{ ckeditor.load() }}
    {{ ckeditor.config(name='comment_body') }}
```

**5. Flask Gravatar**
- Using the `Flask Gravatar` package to turn the saved img_url in the database of the user into a gravatar_url to show the
user image when they comment on a post.
```
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
```

---

## Web-Pages:

---


**1. Header**
- A `Bootstrap` template that allows the user to go to the login, register, about and contact pages.
- It's inherited on each website page.

**2. Footer**
- A `Bootstrap` template that allows the user to go to my Github, Linkedin and Instagram profiles.
- It's dynamic, it changes the year to the current year automatically using `datetime` module.
- It's inherited on each website page.

**3. Homepage**
- Accesses the `blog_posts` table in the database and displays all posts' titles and subtitles, 
which allows users to navigate to a specific post page.
- It's built to have "Older Posts" button, but currently there are only few posts so I will make it functional in the future.

**4. Post Page**
- Also accesses the `blog_posts` table in the database but uses post_id to specify the desired post and displays its content.
- Accesses the `users` and `comments` tables to display the comments on that post and their authors.
- It allows logged-in users only to comment on posts.

**5. Register Page**
- Loads the registration form.
- Checks if the provided credentials already exist.
- If not, hashes the entered password using `Werkzeug`.
- Then saves the user inputs into the database and redirects the user to the login page.

**6. Login Page**
- Loads the login form.
- Checks if the provided email exists in the database.
- If so, checks if they provide the correct password.
- I so, logs in the user and redirects them to the homepage.

**7. Contact Page**
- Loads the contact form.
- Uses one of my emails to email another one with the provided inputs from the user, using Python `SMTP`.

**8. About Page**
- Shows a brief about me and my passion for perfumes and other interests.

---
_Credits to: 100-Days of Code Course on Udemy._