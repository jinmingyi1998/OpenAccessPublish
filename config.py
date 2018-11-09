

class Config:
    # csrf config
    CSRF_ENABLED = True
    SECRET_KEY = 'qe4v^trRAVVO7s1R7W46C8@d5ft$HY45gr'

    # sqlalchemy config
    SQLALCHEMY_DATABASE_URI = 'sqlite:///refer.sqlite3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail config
    MAIL_SERVER = 'smtp.126.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'jinmingyi1998@126.com'
    MAIL_PASSWORD = '19980313jmy'
    ADMINS = ['jinmingyi1998@126.com']
    POSTS_PER_PAGE = 25

