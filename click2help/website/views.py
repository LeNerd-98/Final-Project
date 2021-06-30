import os
from datetime import datetime
from flask import Blueprint, render_template, request, flash, url_for, redirect
from flask_login import login_required, current_user
from .models import BlogPost, Voting, NewsPost, Comments, User
from . import db
from . import app

views = Blueprint('views', __name__)

sp_chars = ["/", "?", "<", ">", "\\", ":", "*", "|", " "]


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    blog_posts = BlogPost.query.order_by(BlogPost.posted_on.desc()).all()
    news_posts = NewsPost.query.order_by(NewsPost.posted_on.desc()).all()
    donations = str(db.session.query(db.func.sum(User.all_donations)).scalar())
    if blog_posts and news_posts:
        first_blog_chars=blog_posts[0].content
        if len(first_blog_chars) > 500:
            first_blog_chars=blog_posts[0].content[0:500]
        first_news_chars=news_posts[0].content
        if len(first_news_chars) > 500:
            first_news_chars=news_posts[0].content[0:500]
        return render_template("home.html", user=current_user, blog_posts=blog_posts, news_posts=news_posts, donations=donations, first_news_chars=first_news_chars, first_blog_chars=first_blog_chars)
    elif news_posts and not blog_posts:
        first_news_chars=news_posts[0].content
        if len(first_news_chars) > 500:
            first_news_chars=news_posts[0].content[0:500]
        return render_template("home.html", user=current_user, blog_posts=blog_posts, news_posts=news_posts, donations=donations, first_news_chars=first_news_chars)
    elif blog_posts and not news_posts:
        first_blog_chars=blog_posts[0].content
        if len(first_blog_chars) > 500:
            first_blog_chars=blog_posts[0].content[0:500]
        return render_template("home.html", user=current_user, blog_posts=blog_posts, news_posts=news_posts, donations=donations, first_blog_chars=first_blog_chars)
    else:
        return render_template("home.html", user=current_user, blog_posts=blog_posts, news_posts=news_posts, donations=donations)
    
@views.route('/about_us')
@login_required
def about_us():
    return render_template('about_us.html', user=current_user)


@views.route('/donations', methods=['GET', 'POST'])
@login_required
def donations():
    if request.method == 'POST':
        donation = request.form.get('donation')
        try : 
            float(donation)
            res = True
        except :
            print("Not a float")
            res = False
        if res == False:
            flash('Please enter a valid number', category='error')
            return redirect(url_for('views.donations'))
        else:
            if "." in str(donation):
                check_donation = donation.rsplit(".", 1)[1]
                if len(check_donation) > 2:
                    flash("Please enter a valid number", category='error')
                    return redirect(url_for('views.donations'))
            flash('Thank you for your donation!', category='success')
            donation = float(donation)
            if current_user.all_donations != 0:
                donation = donation + float(current_user.all_donations)
            current_user.all_donations = str(donation)
            db.session.commit()
            return redirect(url_for('views.home'))
    else:
        return render_template("donations.html", user=current_user)


@views.route('/account')
@login_required
def account():
    image_file = url_for(
        'static', filename='images/' + current_user.image_file)
    return render_template("account.html", user=current_user, image_file=image_file)


@views.route("/<string:posted_by>")
@login_required
def profiles(posted_by):
    profile = User.query.filter_by(user_name=posted_by).first_or_404()
    return render_template('profiles.html', user=current_user, profile=profile)


@views.route('/blog', methods=['GET', 'POST'])
@login_required
def posts():
    page = request.args.get('page', 1, type=int)
    posts = BlogPost.query.order_by(
        BlogPost.posted_on.desc()).paginate(page=page, per_page=5)
    return render_template('blogs.html', posts=posts, user=current_user)


@views.route("/blog/<string:posted_by>")
@login_required
def charity_posts(posted_by):
    page = request.args.get('page', 1, type=int)
    poster = BlogPost.query.filter_by(posted_by=posted_by).first_or_404()
    posts = BlogPost.query.filter_by(posted_by=posted_by).order_by(
        BlogPost.posted_on.desc()).paginate(page=page, per_page=5)
    return render_template('charity_posts.html', posts=posts, user=current_user, poster=poster)


@views.route("/blog/entry/<string:title>")
@login_required
def charity_post_comments(title):
    actual_title = BlogPost.query.filter_by(title=title).first_or_404()
    posts = BlogPost.query.filter_by(title=title).order_by(
        BlogPost.posted_on.desc()).all()
    comments = Comments.query.filter_by(belonging_post=title).order_by(
        Comments.posted_on.desc()).all()
    return render_template('charity_post_comments.html', posts=posts, user=current_user, title=actual_title, comments=comments)


@views.route("blog/entry/create/<string:title>", methods=['GET', 'POST'])
@login_required
def create_comment(title):
    actual_title = BlogPost.query.filter_by(title=title).first_or_404()
    if request.method == 'POST':
        belonging_post = title
        post_content = request.form['comment']
        new_post = Comments(belonging_post=belonging_post, content=post_content,
                                    posted_by=current_user.user_name, posted_on=datetime.now())
        db.session.add(new_post)
        db.session.commit()
        print(belonging_post)
        return redirect(url_for("views.charity_post_comments", title=belonging_post))
    return render_template('create_comment.html', posts=posts, user=current_user, title=actual_title)


def allowed_image(filename):
    if not "." in filename:
        return False
    global ext
    ext = filename.rsplit(".", 1)[1]
    if ext.upper() in app.config['ALLOWED_IMAGE_EXTENSIONS']:
        return True
    else:
        return False


@views.route("/blog/post", methods=['GET', 'POST'])
@login_required
def new_post():
    if current_user.is_charity:
        if request.method == 'POST':
            image = request.files["image"]
            if image:
                if image.filename == "":
                    flash("Image must have a filename", category='error')
                    return redirect(request.url)
                if not allowed_image(image.filename):
                    flash("That image extension is not allowed", category='error')
                    return redirect(request.url)
                else:
                    post_title = request.form['title']
                    post_content = request.form['post']
                    replaced_post_title = post_title
                    for i in sp_chars:
                        replaced_post_title = replaced_post_title.replace(i, '')
                    check_post_title = "blog_picture_"+str(replaced_post_title)+"."+str(ext)
                    to_check = BlogPost.query.filter_by(post_image=check_post_title).all()
                    while to_check:
                        replaced_post_title = str(replaced_post_title)+"1" 
                        check_post_title = "blog_picture_"+str(replaced_post_title)+"."+str(ext)
                        to_check = BlogPost.query.filter_by(post_image=check_post_title).all()
                    image.save(os.path.join(app.root_path, 'static/images', "blog_picture_"+str(replaced_post_title)+"."+str(ext)))
                    new_post = BlogPost(title=post_title, content=post_content,
                                    posted_by=current_user.user_name, posted_on=datetime.now(), post_image = "blog_picture_"+str(replaced_post_title)+"."+str(ext))
                    db.session.add(new_post)
                    db.session.commit()
                    return redirect(url_for('views.posts'))
            else:
                post_title = request.form['title']
                post_content = request.form['post']
                new_post = BlogPost(title=post_title, content=post_content,
                                    posted_by=current_user.user_name, posted_on=datetime.now())
                db.session.add(new_post)
                db.session.commit()
            return redirect(url_for('views.posts'))
        else:
            return render_template('create_post.html', user=current_user)
    else:
        return redirect(url_for('views.posts'))


@views.route('/blog/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    to_edit = BlogPost.query.get_or_404(id)
    if current_user.user_name == to_edit.posted_by:
        if request.method == 'POST':
            image = request.files["image"]
            if image:
                if image.filename == "":
                    flash("Image must have a filename", category='error')
                    return redirect(request.url)
                if not allowed_image(image.filename):
                    flash("That image extension is not allowed", category='error')
                    return redirect(request.url)
                else:
                    post_content = request.form['post'] 
                    image_title = to_edit.title
                    check_post_title = "blog_picture_"+str(image_title)+"."+str(ext)            
                    current_picture = to_edit.post_image
                    if current_picture != "default.jpg" and current_picture:
                        current_picture_path = os.path.join(app.root_path, 'static/images/', current_picture)
                        os.remove(current_picture_path)
                    to_check = BlogPost.query.filter_by(post_image=check_post_title).all()
                    while to_check:
                        image_title = str(image_title)+"1" 
                        check_post_title = "blog_picture_"+str(image_title)+"."+str(ext)
                        to_check = BlogPost.query.filter_by(post_image=check_post_title).all()
                    image.save(os.path.join(app.root_path, 'static/images', "blog_picture_"+str(image_title)+"."+str(ext)))
                    to_edit.content = post_content
                    to_edit.post_image = "blog_picture_"+str(image_title)+"."+str(ext)
                    db.session.commit()
                    return redirect(url_for('views.posts'))
            else:
                to_edit.content = request.form['post']
                db.session.commit()
                return redirect(url_for('views.posts'))
        else:
            return render_template('edit_post.html', post=to_edit, user=current_user)
    else:
        return redirect(url_for('views.posts'))


@views.route('/blog/delete/<int:id>')
@login_required
def delete(id):
    to_delete = BlogPost.query.get_or_404(id)
    if current_user.user_name == to_delete.posted_by or current_user.is_mod:
        Comments.query.filter_by(belonging_post = to_delete.title).delete()
        db.session.delete(to_delete)
        db.session.commit()
        return redirect(url_for('views.posts'))
    

@views.route('/comment/delete/<int:id>')
@login_required
def delete_comment(id):
    to_delete = Comments.query.get_or_404(id)
    if current_user.user_name == to_delete.posted_by or current_user.is_mod:
        db.session.delete(to_delete)
        db.session.commit()
        return redirect(url_for('views.posts'))


@views.route('/voting', methods=['GET', 'POST'])
@login_required
def user_voting():
    if request.method == 'POST':
        if request.form.get('voting_registration') == "+ Register for voting":
            all_candidates = Voting.query.filter_by(
                charity_voting_name=current_user.user_name).first()
            if all_candidates:
                flash('You are already registered.', category='error')
                print(all_candidates.charity_voting_name)
                return redirect(url_for('views.user_voting'))
            else:
                
                new_candidate = Voting(
                    charity_voting_name=current_user.user_name, image_file=current_user.image_file)
                db.session.add(new_candidate)
                db.session.commit()
                print(new_candidate.charity_voting_name)
                return redirect(url_for('views.user_voting'))
        else:
            if request.form.get('vote_casting'):
                candidate = request.form['vote_casting']
                if current_user.has_voted == True:
                    flash('Looks like you already voted', category='error')
                    print(current_user.has_voted)
                    return redirect(url_for('views.user_voting'))
                else:
                    current_user.has_voted = True
                    vote_amount = Voting.query.filter_by(charity_voting_name=candidate).first()
                    vote_amount.votes = vote_amount.votes + 1
                    vote_count = Voting(votes=vote_amount.votes)
                    db.session.commit()
                    print(vote_count.votes, vote_amount)
                    return redirect(url_for('views.user_voting'))
            return redirect(url_for('views.user_voting'))
    else:
        order = Voting.query.order_by(Voting.posted_on).all()
        return render_template("voting.html", user=current_user, order=order)



@views.route('/news', methods=['GET', 'POST'])
@login_required
def news_posts():
    page = request.args.get('page', 1, type=int)
    posts = NewsPost.query.order_by(
        NewsPost.posted_on.desc()).paginate(page=page, per_page=5)
    return render_template('news.html', posts=posts, user=current_user)


@views.route("/news/<string:posted_by>")
@login_required
def mod_posts(posted_by):
    page = request.args.get('page', 1, type=int)
    poster = NewsPost.query.filter_by(posted_by=posted_by).first_or_404()
    posts = NewsPost.query.filter_by(posted_by=posted_by).order_by(
        NewsPost.posted_on.desc()).paginate(page=page, per_page=5)
    return render_template('news_posts.html', posts=posts, user=current_user, poster=poster)


def allowed_image(filename):
    if not "." in filename:
        return False
    global ext
    ext = filename.rsplit(".", 1)[1]
    if ext.upper() in app.config['ALLOWED_IMAGE_EXTENSIONS']:
        return True
    else:
        return False


@views.route("/news/post", methods=['GET', 'POST'])
@login_required
def new_news_post():
    if current_user.is_mod:
        if request.method == 'POST':
            image = request.files["image"]
            if image:
                if image.filename == "":
                    flash("Image must have a filename", category='error')
                    return redirect(request.url)
                if not allowed_image(image.filename):
                    flash("That image extension is not allowed", category='error')
                    return redirect(request.url)
                else:
                    post_title = request.form['title']
                    post_content = request.form['post']
                    replaced_post_title = post_title
                    for i in sp_chars:
                        replaced_post_title = replaced_post_title.replace(i, '')
                    check_post_title = "news_picture_"+str(replaced_post_title)+"."+str(ext)
                    to_check = NewsPost.query.filter_by(news_image=check_post_title).all()
                    while to_check:
                        replaced_post_title = str(replaced_post_title)+"1" 
                        check_post_title = "news_picture_"+str(replaced_post_title)+"."+str(ext)
                        to_check = NewsPost.query.filter_by(news_image=check_post_title).all()
                    image.save(os.path.join(app.root_path, 'static/images', "news_picture_"+str(replaced_post_title)+"."+str(ext)))
                    new_post = NewsPost(title=post_title, content=post_content,
                                    posted_by=current_user.user_name, posted_on=datetime.now(), news_image = "news_picture_"+str(replaced_post_title)+"."+str(ext))
                    db.session.add(new_post)
                    db.session.commit()
                    return redirect(url_for('views.news_posts'))
            else:
                post_title = request.form['title']
                post_content = request.form['post']
                new_post = NewsPost(title=post_title, content=post_content,
                                    posted_by=current_user.user_name, posted_on=datetime.now())
                db.session.add(new_post)
                db.session.commit()
            return redirect(url_for('views.news_posts'))
        else:
            return render_template('create_news.html', user=current_user)
    else:
        return redirect(url_for('views.news_posts'))


@views.route('/news/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    to_edit = NewsPost.query.get_or_404(id)
    if current_user.is_mod:
        if request.method == 'POST':
            image = request.files["image"]
            if image:
                if image.filename == "":
                    flash("Image must have a filename", category='error')
                    return redirect(request.url)
                if not allowed_image(image.filename):
                    flash("That image extension is not allowed", category='error')
                    return redirect(request.url)
                else:
                    post_title = request.form['title']
                    post_content = request.form['post'] 
                    replaced_post_title = post_title
                    for i in sp_chars:
                        replaced_post_title = replaced_post_title.replace(i, '')
                    check_post_title = "news_picture_"+str(replaced_post_title)+"."+str(ext)            
                    current_picture = to_edit.news_image
                    if current_picture != "default.jpg" and current_picture:
                        current_picture_path = os.path.join(app.root_path, 'static/images/', current_picture)
                        os.remove(current_picture_path)
                    to_check = NewsPost.query.filter_by(news_image=check_post_title).all()
                    while to_check:
                        replaced_post_title = str(replaced_post_title)+"1" 
                        check_post_title = "news_picture_"+str(replaced_post_title)+"."+str(ext)
                        to_check = NewsPost.query.filter_by(news_image=check_post_title).all()
                    image.save(os.path.join(app.root_path, 'static/images', "news_picture_"+str(replaced_post_title)+"."+str(ext)))  
                    to_edit.title = post_title
                    to_edit.content = post_content
                    to_edit.news_image = "news_picture_"+str(replaced_post_title)+"."+str(ext)
                    db.session.commit()
                    return redirect(url_for('views.news_posts'))
            else:
                to_edit.title = request.form['title']
                to_edit.content = request.form['post']
                db.session.commit()
                return redirect(url_for('views.news_posts'))
        else:
            return render_template('edit_news.html', post=to_edit, user=current_user)
    else:
        return redirect(url_for('views.news_posts'))


@views.route('/news/delete/<int:id>')
@login_required
def delete_news(id):
    to_delete = NewsPost.query.get_or_404(id)
    if current_user.is_mod:
        db.session.delete(to_delete)
        db.session.commit()
        return redirect(url_for('views.news_posts'))
    else:
        return redirect(url_for('views.news_posts'))