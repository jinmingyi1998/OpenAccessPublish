from flask_login import UserMixin
from app import app, db, lm

ROLE_USER = 0
ROLE_ADMIN = 1


# User class is unavailable
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    email = db.Column(db.String(50))
    password = db.Column(db.String(50))

    def __repr__(self):
        return "user %s %s %s %s" % (self.id, self.username, self.email, self.password)

    def is_authenticated(self):
        return True

    def is_active(self):
        # TO DO:Change return value into a specific value after eamil active has been implemented
        return True

    def is_anonymous(self):
        return False


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(50))
    author = db.Column(db.String(50))
    highlight = db.Column(db.Text)
    keyword = db.Column(db.String(100))
    email = db.Column(db.String(50))
    date = db.Column(db.DateTime)
    pdf = db.Column(db.String(100))
    voteup = db.Column(db.Integer, default=0)
    votedown = db.Column(db.Integer, default=0)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50))
    target = db.Column(db.Integer, db.ForeignKey(Article.id))
    content = db.Column(db.Text)
    date = db.Column(db.DateTime)
    voteup = db.Column(db.Integer, default=0)
    votedown = db.Column(db.Integer, default=0)


class Vote():
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer)
    ip = db.Column(db.String(50))
    date = db.Column(db.DateTime)
    type = db.Column(db.String(50), default="up")


class VoteArticle(Vote, db.Model):
    pass


class VoteComment(Vote, db.Model):
    pass


class BadUser(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    ip = db.Column(db.String(20))


# db.drop_all()
db.create_all()
