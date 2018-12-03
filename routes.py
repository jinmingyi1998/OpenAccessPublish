from app import app, db, lm, mail
from flask import render_template, flash, redirect, g, session, url_for, request, get_flashed_messages, \
    send_from_directory, abort
from forms import *
from models import *
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
import datetime
import re
import os
from threading import Thread


def send_email_background(msg):
    mail.send(msg)


def send_email(msg):
    thr = Thread(target=send_email_background, args=[msg])
    thr.run()


@app.route('/')
def hello_world():
    # print(current_user)
    return render_template('index.html', title="OPEN ACCESS PUBLISHING")


# Login and register are not in using
# @app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        print(form.data)
        print(form.validate())
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data, password=form.password.data).first()
            print('input user is:')
            print(user)
            if user is not None:
                print('-------------------\nTry to login\n-------------------')
                login_user(user, remember=form.remember_me.data)
                flash('Welcome back, ' + user.username)
                return redirect('/')
    return render_template('Login.html', title='Sign in', form=form)


# Login and register are not in using
# @app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            print(form.data)
            user = User.query.filter_by(email=form.email.data).first()
            print(user)
            if user is None:
                user = User(password=form.password.data, email=form.email.data, username=form.username.data)
                print(user)
                print('-------------------\nRegistered\n-------------------')
                db.session.add(user)
                db.session.commit()
                return redirect('/login')
    return render_template('register.html', title='Sign up', form=form)


# Login and register are not in using
# @app.route('/logout')
def logout():
    print('logout : ', end="")
    print(current_user)
    logout_user()
    return redirect('/')


# Login and register are not in using
# @app.before_request
def before_request():
    g.user = current_user


@app.route('/publish', methods=['POST', 'GET'])
def publish():
    form = UploadForm()
    msg = "You should only upload a pdf file"
    if request.method == 'POST':
        if form.validate_on_submit():
            e = Email(email=form.email.data)
            if e.is_exist() and e.is_validated():
                article = form.to_Article()
                article.id = str(1)
                a_num = int(Article.query.count())
                if a_num > 0:
                    article.id = str(int(Article.query.order_by(Article.id.desc()).first().id) + 1)
                article.pdf = str(article.id) + '.pdf'
                filename = os.path.join(app.root_path, "static", "pdf", article.id + '.pdf')
                form.file.data.save(filename)
                db.session.add(article)
                subs = str(article.subject).split(" ")
                print(subs)
                for sut in subs:
                    subject = Subject.query.filter_by(subject=sut).first()
                    if subject is not None:
                        subject.number += 1
                    else:
                        subject = Subject(subject=sut, number=1)
                        db.session.add(subject)
                print(article)
                db.session.commit()
                email_msg = Message(recipients=[form.email.data], subject='[OPEN ACCESS PUBLISH]Publish notification')
                email_msg.body = 'CLICK HERE TO VALIDATE'
                email_msg.html = "<h1>Notification</h1><p>You have published an <a href='http://jinmingyi.xin:8080/detail/%s'>article</a>.</p>" % str(
                    article.id)
                send_email(email_msg)
                return redirect('/detail/' + str(article.id))
            else:
                msg = "You must validate your email address before you publish"

    return render_template('publish.html', form=form, title='Publish', message=msg)


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchArticleForm()
    if request.method == 'POST':
        a = Article(title=form.title.data, author=form.author.data, subject=form.subject.data, email=form.email.data)
        articles = Article.query.filter(Article.title.like("%%%s%%" % a.title),
                                        Article.author.like("%%%s%%" % a.author),
                                        Article.subject.like("%%%s%%" % a.subject),
                                        Article.email.like("%%%s%%" % a.email)).order_by(Article.id.desc()).all()
        return render_template('search.html', list=articles, form=form)
    articles = Article.query.order_by(Article.id.desc()).all()
    return render_template('search.html', list=articles, form=form)


@app.route('/detail/<int:article_id>', methods=['GET', 'POST'])
def detail(article_id):
    form = CommentForm()
    article = Article.query.filter_by(id=article_id).first()
    if article is not None:
        comments = Comment.query.filter_by(target=article.id).order_by(Comment.date.desc()).all()
        if request.method == 'POST':
            if form.validate_on_submit():
                e = Email(email=form.email.data)
                if e.is_exist() and e.is_validated():
                    comment = Comment(target=article.id, content=check_text(form.comment.data), email=form.email.data,
                                      id=1)
                    t_num = int(Comment.query.count())
                    if t_num > 0:
                        comment.id = Comment.query.order_by(Comment.id.desc()).first().id + 1
                    comment.date = datetime.datetime.now()
                    db.session.add(comment)
                    db.session.commit()
                    email_msg = Message(recipients=[e.email], subject="Notification")
                    email_msg.html = """<h1>Notication</h1><p>Your email has made a comment 
                    on <a href='http://jinmingyi.xin:8080/detail/%s'>website</a></p>""" % str(article_id)
                    send_email(email_msg)
                    return redirect('/detail/' + str(article_id))
        return render_template('detail.html', form=form, title='Detail', article=article, comments=comments)
    abort(404)


def check_text(str):
    s = str
    res = BadWord.query.all()
    for r in res:
        s = re.sub(r.word, '  ', s)
    return s


@app.route('/download/<article_pdf>', methods=['GET'])
def download_pdf(article_pdf):
    return send_from_directory('static/pdf', article_pdf)


@app.route('/vote/<target_type>/<vote_type>/<vote_id>', methods=["POST"])
def vote(target_type, vote_type, vote_id):
    if request.method == "POST":
        if vote_type == "up" or vote_type == "down":
            if target_type == "comment":
                if int(Comment.query.filter_by(id=vote_id).count()) > 0:
                    if VoteComment.query.filter_by(target_id=vote_id, ip=request.remote_addr,
                                                   type=vote_type).count() > 0:
                        VoteComment.query.filter_by(target_id=vote_id, ip=request.remote_addr, type=vote_type).delete()
                    else:
                        v = VoteComment(target_id=vote_id, ip=request.remote_addr, date=datetime.datetime.now(), id=1,
                                        type=vote_type)
                        if int(VoteComment.query.count()) > 0:
                            v.id = VoteComment.query.order_by(VoteComment.id.desc()).first().id + 1
                        db.session.add(v)
                    db.session.commit()
                    cnt = VoteComment.query.filter_by(target_id=vote_id, type=vote_type).count()
                    Comment.query.filter_by(id=vote_id).update({'vote' + vote_type: cnt})
                    db.session.commit()
                    return str(cnt)
            elif target_type == "article":
                if Article.query.filter_by(id=vote_id).count() > 0:
                    if VoteArticle.query.filter_by(target_id=vote_id, ip=request.remote_addr,
                                                   type=vote_type).count() > 0:
                        VoteArticle.query.filter_by(target_id=vote_id, ip=request.remote_addr, type=vote_type).delete()
                    else:
                        v = VoteArticle(target_id=vote_id, ip=request.remote_addr, date=datetime.datetime.now(), id=1,
                                        type=vote_type)
                        if VoteArticle.query.count() > 0:
                            v.id = VoteArticle.query.order_by(VoteArticle.id.desc()).first().id + 1
                        db.session.add(v)
                    db.session.commit()
                    cnt = VoteArticle.query.filter_by(target_id=vote_id, type=vote_type).count()
                    Article.query.filter_by(id=vote_id).update({'vote' + vote_type: cnt})
                    db.session.commit()
                    return str(cnt)
    abort(404)


@app.route('/ckvote/<target_type>/<vote_type>/<vote_id>', methods=["POST"])
def ckvote(target_type, vote_type, vote_id):
    if request.method == "POST":
        if vote_type == "up" or vote_type == "down":
            if target_type == "comment":
                if int(Comment.query.filter_by(id=vote_id).count()) > 0:
                    if VoteComment.query.filter_by(target_id=vote_id, ip=request.remote_addr,
                                                   type=vote_type).count() > 0:
                        return "1"
                    else:
                        return '0'
            elif target_type == "article":
                if Article.query.filter_by(id=vote_id).count() > 0:
                    if VoteArticle.query.filter_by(target_id=vote_id, ip=request.remote_addr,
                                                   type=vote_type).count() > 0:
                        return "1"
                    else:
                        return "0"
    abort(404)


@app.route('/validator/<statu>', methods=['GET', 'POST'])
@app.route('/validator/<statu>/<email>', methods=['GET', 'POST'])
def email_validate(statu, email=None):
    if email == None:
        if statu == 'activate':
            form = EmailValidateForm()
            if request.method == 'POST':
                if form.validate_on_submit():
                    return redirect('/validator/validation/%s' % form.email.data)
            return render_template('validate.html', title='Validate the email', form=form)
    else:
        e = Email(email=email)
        if statu == 'validation':
            if not e.is_exist():
                e.generate_password()
                email_msg = Message(recipients=[email], subject='OPEN ACCESS PUBLISH validation ')
                email_msg.body = 'CLICK HERE TO VALIDATE'
                email_msg.html = "<h1>Activation</h1><p><a href='http://jinmingyi.xin:8080/captcha/%s'>Click to activate</a></p>" % e.password
                send_email(email_msg)
                e.validate_time = datetime.datetime.now()
                db.session.add(e)
                db.session.commit()
                return "We've already send you an validation email"
            elif not e.is_validated():
                return "<a href='/validator/resend/%s'>Didn't receive email?</a>" % email
            else:
                abort(404)
        elif statu == 'resend':
            if e.is_exist():
                if not e.is_validated():
                    email_msg = Message(recipients=[email], subject='OPEN ACCESS PUBLISH validation ')
                    email_msg.body = 'CLICK HERE TO VALIDATE'
                    email_msg.html = "<h1>Activation</h1><p><a href='http://jinmingyi.xin:8080/captcha/%s'>Click to activate</a></p>" % e.password
                    send_email(email_msg)
                    return "We've already send you an validation email"
            abort(404)
    abort(404)


@app.route('/captcha/<password>', methods=['GET'])
def validate_captcha(password):
    num = Email.query.filter_by(password=password, validated='no').count()
    if num > 0:
        Email.query.filter_by(password=password).update({'validated': 'yes'})
        db.session.commit()
        return "Activation Success!<a href='/'>Back</a>"
    abort(404)

@app.route('/donate')
def donation():
    return render_template('donate.html',title="Donation")

@app.before_request
def ip_filter():
    ip = request.remote_addr
    if BadUser.query.filter_by(ip=ip).count() > 0:
        abort(403)
    return
