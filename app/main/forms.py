from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField,TextAreaField,SelectField
from flask.ext.pagedown.fields import PageDownField
from wtforms.validators import DataRequired, Length, Email,Regexp,EqualTo
from wtforms import ValidationError
from ..models import User,Role

class EditProfileForm(Form):
	name = StringField('Real Name',validators=[Length(0,64)])
	location = StringField('Location',validators=[Length(0,64)])
	about_me = TextAreaField('About me')

class EditProfileAdminForm(Form):
	email = StringField('Email',validators=[DataRequired(),Length(1,64),Email(message='邮箱格式不正确')])
	username = StringField('Username',validators=[DataRequired(),Length(1,64),\
		Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'不能包含特殊符号！')])
	role = SelectField('Role',coerce=int)
	name = StringField('Real Name',validators=[Length(0,64)])
	location = StringField('Location',validators=[Length(0,64)])
	about_me = TextAreaField('About me')

	def __init__(self,user,*args,**kwargs):
		super(EditProfileAdminForm,self).__init__(*args,**kwargs)
		self.role.choices = [(role.id,role.name) for role in Role.query.order_by(Role.name).all()]
		self.user = user
	def validate_email(self,field):
		if field.data != self.user.email and User.query.filter_by(email=field.data).first():
			raise ValidationError('邮箱已存在！')
	def validate_username(self,field):
		if field.data !=self.user.username and User.query.filter_by(username=field.data).first():
			raise ValidationError('用户名已存在！')

class PostForm(Form):
	body = PageDownField("What's on your mind?",validators=[DataRequired()])
class CommentForm(Form):
	body = TextAreaField('',validators=[DataRequired()])