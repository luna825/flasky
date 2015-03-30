from flask import render_template, redirect, request, url_for, flash
from flask.ext.login import login_user, logout_user,current_user,login_required
from . import auth
from ..models import User
from .forms import LoginForm, RegistrationForm, EditPasswordForm
from .. import db

@auth.before_app_request
def before_request():
	if current_user.is_authenticated():
		current_user.ping()

@auth.route('/login',methods=['GET','POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user, form.remember.data)
			return redirect(request.args.get('next') or url_for('main.user',username=user.username))
		flash('用户名或密码错误')
	return render_template('auth/login.html',form = form)

@auth.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('main.index'))

@auth.route('/register',methods=['GET','POST'])
def register():
	form=RegistrationForm()
	if form.validate_on_submit():
		user = User(email=form.email.data,username=form.username.data,password=form.password.data)
		db.session.add(user)
		u = User.query.filter_by(username=user.username).first()
		login_user(u)
		return redirect(url_for('main.user',username=u.username))
	return render_template('auth/register.html',form=form)

@auth.route('/edit-password',methods=['GET','POST'])
@login_required
def edit_password():
	form = EditPasswordForm()
	if form.validate_on_submit():
		current_user.password = form.newpassword.data
		db.session.add(current_user)
		flash('修改成功')
	return render_template('auth/editpassword.html',form=form)


