from sqlalchemy.orm import defaultload
from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    user_name = db.Column(db.String(150), unique=True)
    displayed_name = db.Column(db.String(150))
    is_user = db.Column(db.Boolean, default=False)
    is_charity = db.Column(db.Boolean, default=False)
    is_mod = db.Column(db.Boolean, default=False)
    is_company = db.Column(db.Boolean, default=False)
    image_file = db.Column(db.String(50), nullable=False, default='default.jpg')
    has_voted = db.Column(db.Boolean, default=False)
    all_donations = db.Column(db.String(100), default="0")
    description = db.Column(db.String(1000), default="")
    street = db.Column(db.String(50), default="")
    postalcode = db.Column(db.String(50), default="")
    city = db.Column(db.String(50), default="")
    link = db.Column(db.String(200), default="")
    phone_number = db.Column(db.String(50), default="")


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    posted_by = db.Column(db.String(150), nullable=False, default='N/A')
    posted_on = db.Column(db.DateTime, nullable=False, default=datetime.now())
    post_image = db.Column(db.String(50))
    def __repr__(self):
        return self.title


class NewsPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    posted_by = db.Column(db.String(150), nullable=False, default='N/A')
    posted_on = db.Column(db.DateTime, nullable=False, default=datetime.now())
    news_image = db.Column(db.String(50))
    def __repr__(self):
        return self.title


class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    belonging_post = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    posted_by = db.Column(db.String(150), nullable=False, default='N/A')
    posted_on = db.Column(db.DateTime, nullable=False, default=datetime.now())
    def __repr__(self):
        return self.belonging_post

class Voting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    charity_voting_name = db.Column(db.String(150), nullable=False, unique=True)
    votes = db.Column(db.Integer, default=0)
    posted_on = db.Column(db.DateTime, nullable=False, default=datetime.now())
    image_file = db.Column(db.String(50), nullable=False)

