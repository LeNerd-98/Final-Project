from operator import pos
import os
from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import BlogPost, Comments, NewsPost, User, Voting
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from . import app
from PIL import Image

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign_up_user', methods=['GET', 'POST'])
def sign_up_user():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('userName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        other_email = User.query.filter_by(email=email).first()
        user = User.query.filter_by(user_name=username).first()
        if other_email:
            flash('Email already exists.', category='error')
        elif user:
            flash('Username already exists', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(username) < 2:
            flash('User name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, user_name=username, displayed_name=username, password=generate_password_hash(
                password1, method='sha256'), is_user=True)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up_user.html", user=current_user)

def allowed_image(filename):
    if not "." in filename:
        return False
    global ext
    ext = filename.rsplit(".", 1)[1]
    if ext.upper() in app.config['ALLOWED_IMAGE_EXTENSIONS']:
        return True
    else:
        return False


def crop_center(im, crop_width, crop_height):
    img_width, img_height = im.size
    return im.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


def crop_max_square(im):
    return crop_center(im, min(im.size), min(im.size))


@auth.route('/update_image', methods=['GET', 'POST'])
@login_required
def update_image():
    if request.method == 'POST':
        if request.files:
            image = request.files["image"]
            if image.filename == "":
                flash("Image must have a filename", category='error')
                return redirect(request.url)
            
            if not allowed_image(image.filename):
                flash("That image extension is not allowed", category='error')
                return redirect(request.url)
            
            else:
                filename = secure_filename(image.filename) 
                                
                current_picture = current_user.image_file
                current_picture_path = os.path.join(app.root_path, 'static/images/', current_picture)
                if current_picture != "default.jpg":
                    os.remove(current_picture_path)

                image.save(os.path.join(app.root_path, 'static/images', "profile_picture_"+str(current_user.id)+"."+str(ext)))
                im = Image.open(os.path.join(app.root_path, 'static/images/', "profile_picture_"+str(current_user.id)+"."+str(ext)))
                
                new_size = crop_max_square(im).resize((300,300), Image.LANCZOS)
                new_size.save(os.path.join(app.root_path, 'static/images', "profile_picture_"+str(current_user.id)+"."+str(ext)))
                flash("Image Saved", category='success')

                current_user.image_file = "profile_picture_"+str(current_user.id)+"."+str(ext)
                db.session.commit()
                return redirect(url_for('views.account'))
               
        else:
            current_picture = current_user.image_file
            current_picture_path = os.path.join(app.root_path, 'static/images/', current_picture)
            if current_picture != "default.jpg":
                    os.remove(current_picture_path)
            default_picture = "default.jpg"
            current_user.image_file = default_picture
            db.session.commit()
            return redirect(url_for('views.account'))
    else:
        return render_template("update_image.html", user=current_user)


@auth.route('/update_user', methods=['GET', 'POST'])
@login_required
def update_user():
    email = request.form.get('email')
    user_name = request.form.get('userName')
    description = request.form.get('description')
    street = request.form.get('street')
    postalcode = request.form.get('postalcode')
    city = request.form.get('city')
    link = request.form.get('link')
    phone_number = request.form.get('phone_number')
    if request.method == 'POST':
        other_email = User.query.filter_by(email=email).first()
        user = User.query.filter_by(user_name=user_name).first()
        if (len(email) < 4):
            flash('Email must be greater than 3 characters.', category='error')
        elif user and user_name != current_user.user_name:
            flash("This username has already been used", category='error')
        elif other_email and email != current_user.email:
            flash('This Email already exists.', category='error')
        elif len(user_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        else:
            current_user.email = email
            current_user.diplayed_name = user_name
            current_user.description = description
            current_user.street = street
            current_user.postalcode = postalcode
            current_user.city = city
            current_user.link = link
            current_user.phone_number = phone_number
            db.session.commit()
            flash('Account successfully updated!', category='success')
            return redirect(url_for('views.account'))

    return render_template("update_user.html", user=current_user)


@auth.route('/sign_up_sponsor', methods=['GET', 'POST'])
def sign_up_sponsor():
    if request.method == 'POST':
        email = request.form.get('email')
        company_name = request.form.get('CompanyName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        other_email = User.query.filter_by(email=email).first()
        user = User.query.filter_by(user_name=company_name).first()
        if other_email:
            flash('Email already exists.', category='error')
        elif user:
            flash('This name has already been used', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(company_name) < 2:
            flash('Company name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, user_name=company_name, displayed_name=company_name, password=generate_password_hash(
                password1, method='sha256'), is_company=True)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up_sponsor.html", user=current_user)


@auth.route('/sign_up_charity', methods=['GET', 'POST'])
def sign_up_charity():
    if request.method == 'POST':
        email = request.form.get('email')
        charity_name = request.form.get('CharityName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        other_email = User.query.filter_by(email=email).first()
        user = User.query.filter_by(user_name=charity_name).first()
        if other_email:
            flash('Email already exists.', category='error')
        elif user:
            flash('This name has already been used', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(charity_name) < 2:
            flash('Charity name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, user_name=charity_name, displayed_name=charity_name, password=generate_password_hash(
                password1, method='sha256'), is_charity=True)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up_charity.html", user=current_user)


@auth.route('/sign_up_mod', methods=['GET', 'POST'])
def sign_up_mod():
    if request.method == 'POST':
        email = request.form.get('email')
        mod_name = request.form.get('ModName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        other_email = User.query.filter_by(email=email).first()
        user = User.query.filter_by(user_name=mod_name).first()
        if other_email:
            flash('Email already exists.', category='error')
        elif user:
            flash('This name has already been used', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(mod_name) < 2:
            flash('Moderator name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, user_name=mod_name, displayed_name=mod_name, password=generate_password_hash(
                password1, method='sha256'), is_mod=True)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up_mod.html", user=current_user)