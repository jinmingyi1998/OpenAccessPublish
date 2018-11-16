from app import app, db, lm
from flask import render_template, flash, redirect, g, session, url_for, request, get_flashed_messages, \
    send_from_directory,abort
from forms import LoginForm, RegisterForm, UploadForm, CommentForm, SearchArticleForm
from models import User, Article, Comment, VoteArticle, VoteComment,BadUser
from flask_login import login_user, logout_user, current_user, login_required
import datetime


@app.route('/')
def hello_world():
    print('index:')
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
    if request.method == 'POST':
        if form.validate_on_submit():
            print(form.email.data, end=' ')
            print(form.title.data)
            article = form.to_Article()
            article.id = str(1)
            a_num = int(Article.query.count())
            if a_num > 0:
                article.id = str(int(Article.query.order_by(Article.id.desc()).first().id) + 1)
            article.pdf = str(article.id) + '.pdf'
            filename = 'static/pdf/' + article.id + '.pdf'
            form.file.data.save(filename)
            db.session.add(article)
            db.session.commit()
            # redirect is not sure
            return redirect('/')

    return render_template('publish.html', form=form, title='Publish')


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchArticleForm()
    if request.method == 'POST':
        print(form.data)
        a = Article(title=form.title.data, author=form.author.data, keyword=form.keyword.data, email=form.email.data)
        articles = Article.query.filter(Article.title.like("%%%s%%" % a.title),
                                        Article.author.like("%%%s%%" % a.author),
                                        Article.keyword.like("%%%s%%" % a.keyword),
                                        Article.email.like("%%%s%%" % a.email)).order_by(Article.id.desc()).all()
        return render_template('search.html', list=articles, form=form)
    articles = Article.query.all()
    return render_template('search.html', list=articles, form=form)


@app.route('/detail/<int:article_id>', methods=['GET', 'POST'])
def detail(article_id):
    form = CommentForm()
    article = Article.query.filter_by(id=article_id).first()
    if article is not None:
        comments = Comment.query.filter_by(target=article.id).order_by(Comment.date.desc()).all()
        if request.method == 'POST':
            if form.validate_on_submit():
                print(form.email.data)
                print('------------------')
                print(form.comment.data)
                comment = Comment(target=article.id, content=form.comment.data, email=form.email.data, id=1)
                t_num = int(Comment.query.count())
                if t_num > 0:
                    comment.id = Comment.query.order_by(Comment.id.desc()).first().id + 1
                comment.date = datetime.datetime.now()
                db.session.add(comment)
                db.session.commit()
                return redirect('/detail/' + str(article_id))
        return render_template('detail.html', form=form, title='Detail', article=article, comments=comments)
    else:
        abort(404)


@app.route('/download/<article_pdf>', methods=['GET'])
def download_pdf(article_pdf):
    return send_from_directory('static/pdf', article_pdf)


@app.route('/vote/<target_type>/<vote_type>/<vote_id>', methods=["POST"])
def vote(target_type, vote_type, vote_id):
    if request.method == "POST":
        if vote_type == "up" or vote_type == "down":
            if target_type == "comment":
                if int(Comment.query.filter_by(id=vote_id).count()) > 0:
                    if VoteComment.query.filter_by(target_id=vote_id, ip=request.remote_addr,type=vote_type).count() > 0:
                        VoteComment.query.filter_by(target_id=vote_id, ip=request.remote_addr,type=vote_type).delete()
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
                    if VoteArticle.query.filter_by(target_id=vote_id, ip=request.remote_addr,type=vote_type).count() > 0:
                        VoteArticle.query.filter_by(target_id=vote_id, ip=request.remote_addr,type=vote_type).delete()
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
                    if VoteComment.query.filter_by(target_id=vote_id, ip=request.remote_addr,type=vote_type).count() > 0:
                        return "1"
                    else:
                        return '0'
            elif target_type == "article":
                if Article.query.filter_by(id=vote_id).count() > 0:
                    if VoteArticle.query.filter_by(target_id=vote_id, ip=request.remote_addr,type=vote_type).count() > 0:
                        return "1"
                    else:
                        return "0"
    abort(404)

@app.before_request
def ip_filter():
    ip=request.remote_addr
    if BadUser.query.filter_by(ip=ip).count() > 0:
        abort(403)
    return