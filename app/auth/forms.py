from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email,Regexp,EqualTo
from wtforms import ValidationError
from ..models import User
from flask.ext.login import current_user

class LoginForm(Form):
	email = StringField('Email',validators=\
		[DataRequired(message='请输入用户名'),Length(1,64),Email(message='请输入正确的邮箱')])
	password = PasswordField('Password',validators=[DataRequired(message='请输入密码')])
	remember = BooleanField('Keep me logged in')

class RegistrationForm(Form):
	email = StringField('Email',validators=[DataRequired(),Length(1,64),Email(message='请输入正确的邮箱')])
	username = StringField('Username',validators=[DataRequired(),Length(1,64),\
		Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'不能包含特殊符号！')])
	password = PasswordField('Password',validators=[DataRequired(),EqualTo('password2',message='Password must match')])
	password2 = PasswordField('Confirm password',validators=[DataRequired()])

	def validate_email(self,field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('邮箱已注册！')
	def validate_username(self,field):
		if User.query.filter_by(username=field.data).first():
			raise ValidationError('用户名已存在！')

class EditPasswordForm(Form):
	oldpassword = PasswordField('Oldpassword',validators=[DataRequired()])
	newpassword = PasswordField('Newpassword',validators=[DataRequired(),EqualTo('newpassword2',message='Password must match')])
	newpassword2 = PasswordField('Confirm password',validators=[DataRequired()])

	def validate_oldpassword(self,field):
		if not current_user.verify_password(field.data):
			raise ValidationError('密码错误！')