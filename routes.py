from app import app, db, lm, mail
from flask import render_template, flash, redirect, g, request, send_from_directory, abort, session
from forms import *
from models import *
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
import datetime
import re
import os
from threading import Thread
from tools import *


def send_email_background(msg):
    mail.send(msg)


def send_email(msg):
    thr = Thread(target=send_email_background, args=[msg])
    thr.run()


@app.route('/')
def hello_world():
    arts = Article.query.filter_by(is_hide='no').all()
    for a in arts:
        a.getVisit()
        a.getPoint()
    arts = sorted(arts)
    return render_template('index.html', title="OPEN ACCESS PUBLISHING", articles=arts)


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


# using session to limit repeat request
def check_session(limit=5):
    t1 = 0;
    if session.get('timestamp') is not None:
        t1 = session.get('timestamp')
    delta = time.time() - t1
    session['timestamp'] = time.time()
    if (delta > limit):
        return True
    return False


# publish an article
@app.route('/publish', methods=['POST', 'GET'])
def publish():
    if not check_session(3):
        abort(404)
    form = UploadForm()
    captcha = getCaptcha()
    msg = "You should only upload a pdf file"
    if request.method == 'POST':
        if form.validate_on_submit():
            e = Email(email=form.email.data)
            if e.is_exist() and e.is_validated():
                # generate an article
                article = form.to_Article()
                article.id = str(1)
                a_num = int(Article.query.count())
                if a_num > 0:
                    article.id = str(int(Article.query.order_by(Article.id.desc()).first().id) + 1)
                article.pdf = str(article.id) + '.pdf'
                filename = os.path.join(app.root_path, "static", "pdf", article.id + '.pdf')
                form.file.data.save(filename)
                db.session.add(article)

                # generate a record
                record = IpRecord()
                record.ip = request.remote_addr
                record.page = "publish"
                record.target_id = int(article.id)
                db.session.add(record)

                db.session.commit()

                # send email
                email_msg = Message(recipients=[form.email.data], subject='[OPEN ACCESS PUBLISH]Publish notification')
                email_msg.body = 'CLICK HERE TO VALIDATE'
                email_msg.html = "<h1>Notification</h1><p>You have published an <a href='http://jinmingyi.xin:8080/detail/%s'>article</a></p>" % (
                    str(
                        article.id))
                send_email(email_msg)

                return redirect('/detail/' + str(article.id))
            else:
                msg = "You must activate your email address before you publish"

    return render_template('publish.html', form=form, title='Publish', message=msg, captcha=captcha)


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchArticleForm()
    if request.method == 'POST':
        content = form.content.data
        a = Article(title=content, author=content, subject=content, email=content)
        articles = Article.query.filter(Article.title.like("%%%s%%" % a.title) |
                                        Article.author.like("%%%s%%" % a.author) |
                                        Article.subject.like("%%%s%%" % a.subject)).order_by(Article.id.desc()).all()
        comments = Comment.query.filter(Comment.content.like("%%%s%%" % content)).all()
        return render_template('search.html', list=articles, form=form, commentlist=comments)
    articles = Article.query.filter_by(is_hide='no').order_by(Article.id.desc()).all()
    return render_template('search.html', list=articles, form=form)


@app.route('/detail/<int:article_id>', methods=['GET', 'POST'])
def detail(article_id):
    captcha = getCaptcha()
    form = CommentForm()
    article = Article.query.filter_by(id=article_id).first()
    if article is not None:
        record = IpRecord()
        record.page = "detail"
        record.ip = request.remote_addr
        record.target_id = article_id
        db.session.add(record)
        db.session.commit()
        vis = int(IpRecord.query.filter_by(target_id=article_id, page="detail").group_by("ip").count())
        article.visit = vis
        comments = Comment.query.filter_by(target=article.id).order_by(Comment.date.desc()).all()
        if request.method == 'POST':  # post a comment
            if form.validate_on_submit() and check_session():
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
                    # email actions
                    email_msg = Message(recipients=[e.email], subject="Notification")
                    email_msg.html = """<h1>Notication</h1><p>Your email has made a comment 
                    on <a href='http://jinmingyi.xin:8080/detail/%s'>website</a></p>""" % str(article_id)
                    send_email(email_msg)

                    return redirect('/detail/' + str(article_id))
        return render_template('detail.html', form=form, title='Detail', article=article, comments=comments,
                               captcha=captcha)
    abort(404)


def check_text(str):
    s = str
    res = BadWord.query.all()
    for r in res:
        s = re.sub(r.word, '  ', s)
    return s


@app.route('/download/<article_pdf>', methods=['GET'])
def download_pdf(article_pdf):
    if not check_session():
        abort(404)
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
    return render_template('donate.html', title="Donation")


@app.route('/captcha', methods=['GET', 'POST'])
def checkCaptcha():
    if request.method == 'POST':
        return getCaptcha()
    abort(400)


@app.before_request
def ip_filter():
    ip = request.remote_addr
    if BadUser.query.filter_by(ip=ip).count() > 0:
        abort(403)
    return


@app.route('/author')
def authorpage():
    email = request.args.get('email')
    a = Article.query.filter_by(email=email).all()
    c = Comment.query.filter_by(email=email).all()
    return render_template('author.html', title='Author Page', article=a, comment=c, email=email)
