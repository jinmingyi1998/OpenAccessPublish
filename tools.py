import shutil
from app import app, db, lm, mail
from flask import render_template, abort, url_for, redirect
from models import *
import datetime

import os


class Table:
    def __init__(self):
        self.name = ''
        self.thead = []
        self.items = []


class CommentTable(Table):
    def __init__(self):
        super().__init__()
        self.name = 'comment'
        self.thead.append('ID')
        self.thead.append("email")
        self.thead.append('target')
        self.thead.append('content')
        self.thead.append("date")
        self.thead.append('voteup')
        self.thead.append('votedown')
        comments = Comment.query.all()
        for c in comments:
            row = []
            row.append(c.id)
            row.append(c.email)
            row.append(c.target)
            row.append(c.content)
            row.append(c.date)
            row.append(c.voteup)
            row.append(c.votedown)
            self.items.append(row)


class ArticleTable(Table):
    def __init__(self):
        super().__init__()
        self.name = 'article'
        self.thead.append('ID')
        self.thead.append('Title')
        self.thead.append('Author')
        self.thead.append('Highlight')
        self.thead.append('Subject')
        self.thead.append('Email')
        self.thead.append('Date')
        self.thead.append('Pdf')
        self.thead.append('voteup')
        self.thead.append('votedown')
        articles = Article.query.all()
        for a in articles:
            row = []
            row.append(a.id)
            row.append(a.title)
            row.append(a.author)
            row.append(a.highlight)
            row.append(a.subject)
            row.append(a.email)
            row.append(a.date)
            row.append(a.pdf)
            row.append(a.voteup)
            row.append(a.votedown)
            self.items.append(row)


def remove_captcha():
    for file in os.listdir("static/captcha"):
        os.unlink("static/captcha/" + file)


def remove_article(id):
    a = Article.query.filter_by(id=id).first()
    if a is not None:
        os.unlink('static/pdf/' + a.pdf)  # remove files
        vote = VoteArticle.query.filter_by(target_id=a.id).all()
        for v in vote:  # remove related votes
            db.session.delete(v)
        comments = Comment.query.filter_by(target=a.id).all()
        for c in comments:  # remove related comments
            db.session.delete(c)
        db.session.delete(a)
        db.session.commit()
        return True
    return False


def remove_comment(id):
    c = Comment.query.filter_by(id=id).first()
    if c is not None:
        vote = VoteComment.query.filter_by(target_id=c.id).all()
        for v in vote:
            db.session.delete(v)
        db.session.delete(c)
        db.session.commit()
        return True
    return False


@app.route('/admin/<action>')
@app.route('/admin')
def administrator(action=None):
    if action is None:
        return render_template("admin.html", title="Admin", table=None)
    elif action == 'captcha':
        remove_captcha()
        return "yes"
    elif action == 'articles':
        a = ArticleTable()
        return render_template("admin.html", title="Admin", table=a)

    elif action == 'comments':
        c = CommentTable()
        return render_template("admin.html", title="Admin", table=c)
    abort(404)


# future work:add permission check
@app.route('/admin/delete/<int:id>/<type>')
def admin_remove(id, type):
    print(id)
    print(type)
    if type == 'article':
        if remove_article(id):
            return "yes"
    elif type == 'comment':
        if remove_comment(id):
            return "yes"
    abort(404)
