from flask_wtf.form import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired, FileField
from wtforms import PasswordField, SubmitField, TextAreaField, StringField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp
from models import Article
import datetime


# Login and Register is unavailable
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()], render_kw={'placeholder': 'Email'})
    password = PasswordField("Password", validators=[DataRequired(),
                                                     Regexp("^[a-zA-Z0-9_]{6,15}$")],
                             render_kw={'placeholder': 'Password'})
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Sign in")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message="email error")],
                        render_kw={'placeholder': 'Email'})
    password = PasswordField("Password", validators=[DataRequired(),
                                                     Regexp("^[a-zA-Z0-9_]{5,15}$", message="Regexp_password")],
                             render_kw={'placeholder': 'Password', 'pattern': '^\w{5,15}$'})
    password_again = PasswordField("Repeat Password", validators=[DataRequired(), EqualTo('password')],
                                   render_kw={'placeholder': 'Repeat Password'})
    username = StringField("Username", validators=[DataRequired(),
                                                   Regexp("^[a-zA-Z][a-zA-Z0-9_]{5,15}$", message="regexp_usrname")],
                           render_kw={'placeholder': 'Username', 'pattern': '^[a-zA-Z][a-zA-Z0-9_]{4,15}$'})
    submit = SubmitField("Sign up")


class UploadForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=3, max=50)])
    author = StringField("Author", validators=[DataRequired()])
    keyword = StringField("Keywords", validators=[DataRequired()])
    highlight = TextAreaField("Highlight")
    email = StringField("Email", validators=[DataRequired(), Email(message="email error")],
                        render_kw={'placeholder': 'Email'})
    file = FileField("File", validators=[FileRequired(), FileAllowed(['pdf'])])
    submit = SubmitField("Submit", render_kw={'class': 'btn btn-primary'})

    def to_Article(self):
        return Article(title=self.title.data, author=self.author.data, highlight=self.highlight.data,
                       keyword=self.keyword.data, date=datetime.datetime.now(), email=self.email.data)


class CommentForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message="email error")],
                        render_kw={'placeholder': 'Email'})
    comment = TextAreaField("Comment",
                            validators=[DataRequired(), Length(min=5, max=200, message='At least 5 letters!')])
    submit = SubmitField("Submit", render_kw={'class': 'btn btn-primary'})


class SearchArticleForm(FlaskForm):
    title = StringField("Title")
    author = StringField("Author")
    keyword = StringField("Keywords")
    email = StringField("Author Email", render_kw={'placeholder': 'Email'})
    submit = SubmitField("Submit", render_kw={'class': 'btn btn-primary'})

class EmailValidateForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message="email error")],
                        render_kw={'placeholder': 'Email'})
    submit = SubmitField("Submit", render_kw={'class': 'btn btn-primary'})
