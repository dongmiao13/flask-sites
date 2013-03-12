#!/usr/bin/env python
# -*- coding: utf-8 -*-


from flask import request
from flask import session
from flask import g
from flask import redirect
from flask import url_for
from flask import abort
from flask import render_template
from flask import flash
from sqlalchemy import or_

from settings import db
from settings import app
from models import User
from models import Site
from models import Tag
from utils import get_or_create_tag


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password != confirm_password:
            error = 'confirm password'
        else:
            user = User(username, email, password)
            db.session.add(user)
            db.session.commit()
            flash('Signup successfully')
            return redirect(url_for('login'))
    else:
        return render_template('register.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email, password=password).first()
        if user is None:
            error = 'Invalid email or password'
        else:
            session['logged_in'] = True
            session['user'] = user
            flash('You were logged in')
            return redirect('/')
    return render_template('login.html', error=error)


@app.route('/add', methods=['GET', 'POST'])
def add_site():
    if not session.get('logged_in'):
        abort(401)

    error = None
    if request.method == 'POST':
        title = request.form.get('title', '')
        website = request.form.get('url', '')
        description = request.form.get('description', '')
        source_url = request.form.get('source_url', '')
        tags_names = request.form.get('tags', '').split(',')
        tags_names = filter(lambda s: s, [tag.strip() for tag in tags_names])

        # Add site info to db
        site = Site(title=title, website=website, description=description,
                    source_url=source_url, create_by=session['user'])
        for tag in map(get_or_create_tag, tags_names):
            site.tags.append(tag)
        db.session.add(site)
        db.session.commit()

        flash('New site was successfully added')
        return redirect(url_for('show_sites'))
    else:
        return render_template('add_site.html', error=None)


@app.route('/')
@app.route('/sites/')
def all_sites(mine=False, keyword=None, tag_name=None):
    sites = None
    if mine:
        query = Site.query.filter_by(create_by=session['user'])
    elif keyword:
        query = Site.query.filter(or_(Site.title.like('%%%s%%') % keyword,
                                      Site.description.like('%%%s%%') % keyword
                                      ))
    elif tag_name:
        tag = Tag.query.filter_by(name=tag_name).first()
        sites = tag.sites
    else:
        query = Site.query

    if sites is None:
        sites = query.order_by(Site.create_at.desc()).all()

    return render_template('index.html', sites=sites)


@app.route('/mine/')
def mine():
    if not session.get('logged_in'):
        abort(401)
    else:
        return all_sites(mine=True)


@app.route('/search/')
def search():
    keyword = request.args.get('q')
    if not keyword:
        return redirect('/')
    else:
        return all_sites(keyword=keyword)


@app.route('/tagged/<tag_name>/')
def tagged(tag_name):
    return all_sites(tag_name=tag_name)


@app.route('/site/<int:site_id>')
def show_site(site_id):
    site = Site.query.filter_by(id=site_id).first()
    return render_template('detail.html', site=site)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user', None)
    flash('You were logged out')
    return redirect(url_for('show_sites'))

if __name__ == '__main__':
    app.run()
