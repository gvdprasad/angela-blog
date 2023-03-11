import app as app
from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor,CKEditorField
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm
# from flask_gravatar import Gravatar
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired,URL,Email
from functools import wraps
from flask import abort
from flask_gravatar import Gravatar

login =False
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)
##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
##CONFIGURE TABLES


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    # author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    author_id = db.Column(db.Integer,db.ForeignKey("users.id"))
    author = relationship("User",back_populates="posts")
    comments = relationship("Comment",back_populates="parent_post")

class User(UserMixin, db.Model):
    __tablename__ ="users"
    id =db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250),nullable=False,unique=True)
    password = db.Column(db.String(250),nullable=False)

    posts = relationship("BlogPost",back_populates="author")
    comments = relationship("Comment",back_populates="comment_author")

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text,nullable=False)
    author_id = db.Column(db.Integer,db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    parent_post = relationship("BlogPost",back_populates="comments")
    post_id = db.Column(db.Integer,db.ForeignKey("blog_posts.id"))

with app.app_context():
    db.create_all()
    # new_table = BlogPost(
    #     id = 1,
    #     author_id =1,
    #     title = "The Life of Cactus",
    #     subtitle = "Who knew that cacti lived such interesting lives.",
    #     date="october 20, 2020",
    #     body="<p>Nori grape silver beet broccoli kombu beet greens fava bean potato quandong celery.</p><p>Bunya nuts black-eyed pea prairie turnip leek lentil turnip greens parsnip.</p><p>Sea lettuce lettuce water chestnut eggplant winter purslane fennel azuki bean earthnut pea sierra leone bologi leek soko chicory celtuce parsley j&iacute;cama salsify.</p>",
    #     img_url = "https://images.unsplash.com/photo-1530482054429-cc491f61333b?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1651&q=80",
    #     )
    # db.session.add(new_table)
    # db.session.commit()
class register_form(FlaskForm):
    form_email = StringField("email", validators=[DataRequired(),Email()])
    form_name = StringField("name",validators=[DataRequired()])
    password =StringField("password",validators=[DataRequired()])
    submit = SubmitField("SignMeUp")

class login_form(FlaskForm):
    form_name = register_form.form_name
    password = register_form.password
    submit = SubmitField("LetMeIn")

class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment",validators =[DataRequired()])
    submit = SubmitField("submit comment")


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    users =User.query.all()
    return render_template("index.html", all_posts=posts,logged_in=current_user.is_authenticated)


@app.route('/register',methods=["GET","POST"])
def register():
    form=register_form()
    if form.validate_on_submit():
        email = form.form_email.data
        user = User.query.filter_by(email=email).first()
        if  user:
            flash("user already exists,please login ")
        else:
            new_user =User(
            name = form.form_name.data,
            email = form.form_email.data,
            password = generate_password_hash(
                form.password.data,
                method= 'pbkdf2:sha256',
                salt_length=8
            ))
            db.session.add(new_user)
            db.session.commit()
            print("added user")
            # login_user(new_user)
            return redirect(url_for("login"))





    return render_template("register.html",form=form,logged_in=current_user.is_authenticated)


@app.route('/login',methods=["GET","POST"])
def login():
    login =True
    form = login_form()
    if form.validate_on_submit():
        email= form.form_name.data
        password = form.password.data
        print(email)
        user = User.query.filter_by(email=email).first()
        if not user:
            print("not user")
            flash("invalid user,please try again")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password,password):
            print("wrong password")
            flash("password incorrect,please try again")
            return redirect(url_for('login'))
        else:
            print('successfully login')
            login_user(user)
            return redirect(url_for('get_all_posts'))


    return render_template("login.html",form=form,logged_in=current_user.is_authenticated,login=login)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=["POST","GET"])
def show_post(post_id):
    comment_form= CommentForm()
    requested_post = BlogPost.query.get(post_id)
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("you need to login or register to comment")
            return redirect(url_for("login"))

        new_comment = Comment(
            text = comment_form.comment_text.data,
            comment_author = current_user,
            parent_post = requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post',post_id=post_id))

    return render_template("post.html",form=comment_form, post=requested_post)
#
# @app.route("/post/<int:post_id>",methods=["POST","GET"])
# def comments():
#     comment_form = CommentForm()
#     if comment_form.validate_on_submit():
#


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post",methods=["GET", "POST"])
@admin_only
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


@app.route("/edit-post/<int:post_id>",methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
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
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
