from flask import url_for
from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin, AnonymousUserMixin
from . import login_manager
from markdown import markdown
import bleach

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class Permission:
	FOLLOW = 0x01
	COMMENT= 0x02
	WRITE_ARTICLES = 0x04
	MODERATE_COMMENTS = 0x08
	ADMINISTER = 0x80

class Follow(db.Model):
	__tablename__='follows'
	#关注人的ID
	follower_id = db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
	#被关注人的ID
	followed_id = db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
	timestamp = db.Column(db.DateTime,default = datetime.utcnow)

class User(UserMixin,db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key = True)
	email = db.Column(db.String(64),unique = True, index=True)
	username = db.Column(db.String(64),unique = True,index = True)
	password_hash = db.Column(db.String(128))
	role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
	name =db.Column(db.String(64))
	location = db.Column(db.String(64))
	about_me = db.Column(db.Text())
	member_since = db.Column(db.DateTime(),default=datetime.utcnow)
	last_seen = db.Column(db.DateTime(),default = datetime.utcnow)
	comments = db.relationship('Comment',backref='author',lazy='dynamic')
	posts = db.relationship('Post',backref='author',lazy='dynamic')
	#关注了许多人，把这个人通过ID关联反给FOLLOW
	followed = db.relationship('Follow',foreign_keys=[Follow.follower_id],
		backref=db.backref('follower',lazy='joined'),lazy='dynamic')
	#被许多人关注，把这个人能过ID反给FOLLOW
	followers = db.relationship('Follow',foreign_keys=[Follow.followed_id],
		backref=db.backref('followed',lazy='joined'),lazy='dynamic')

	def is_following(self,user):
		return self.followed.filter_by(followed_id=user.id).first()\
		 is not None
	def is_followed_by(self,user):
		 return self.followers.filter_by(follower_id=user.id).first()\
		 is not None
	
	def follow(self,user):
		if not self.is_following(user):
			f = Follow(follower=self,followed=user)
			db.session.add(f)
	
	def unfollow(self,user):
		f=self.followed.filter_by(followed_id=user.id).first()
		if f:
			db.session.delete(f)
	@property
	def followed_posts(self):
		return Post.query.join(Follow,Follow.followed_id==Post.author_id)\
		.filter(Follow.follower_id==self.id)

	@property
	def password(self):
	    raise AttributeError('password is not a redable attribute')

	@password.setter
	def password(self, password):
	    self.password_hash = generate_password_hash(password)
	def verify_password(self,password):
		return check_password_hash(self.password_hash,password)

	def can(self,permissions):
		return self.role is not None and (self.role.permissions & permissions)==permissions
	def is_administrator(self):
		return self.can(Permission.ADMINISTER)

	def ping(self):
		self.last_seen = datetime.utcnow()
		db.session.add(self)

	def gravatar(self,size='l'):
		if size == 's':
			return url_for('static',filename='img/def-head.jpg')
		else:
			return url_for('static',filename='img/def-head.jpg')

	@staticmethod
	def generate_fake(count=100):
		from sqlalchemy.exc import IntegrityError
		from random import seed
		import forgery_py

		seed()
		for i in range(count):
			u = User(email=forgery_py.internet.email_address(),
					username=forgery_py.internet.user_name(),
					password=forgery_py.lorem_ipsum.word(),
					name=forgery_py.name.full_name(),
					location=forgery_py.address.city(),
					about_me=forgery_py.lorem_ipsum.sentence(),
					member_since=forgery_py.date.date(True))
			db.session.add(u)
			try:
				db.session.commit()
			except IntegrityError:
				db.session.rollback()

	@staticmethod
	def Initialize_follow(username,count=50):
		user = User.query.filter_by(username=username).first()
		if not user:
			print('没有这个用户!')
		else:
			users = User.query.all()[:count]
			for u in users:
				if u.id !=user.id:
					user.follow(u)
					u.follow(user)
			print('互相关注初始化完闭！')


	def __init__(self, **kwargs):
		super(User,self).__init__(**kwargs)
		if self.role is None:
			if self.email =='luna825@qq.com':
				self.role = Role.query.filter_by(permissions=0xff).first()
			if self.role is None:
				self.role = Role.query.filter_by(default=True).first()

class AnonymousUser(AnonymousUserMixin):
	def can(self,permissions):
		return False
	def is_administrator(self):
		return False
login_manager.anonymous_user = AnonymousUser

class Role(db.Model):
	__tablename__='roles'
	id = db.Column(db.Integer,primary_key=True)
	name = db.Column(db.String(64),unique=True)
	default = db.Column(db.Boolean,default=False,index=True)
	permissions = db.Column(db.Integer)
	users = db.relationship('User',backref='role',lazy='dynamic')

	@staticmethod
	def insert_roles():
		roles = {
			'User':(Permission.FOLLOW|Permission.COMMENT|Permission.WRITE_ARTICLES,True),
			'Moderator':(Permission.FOLLOW|Permission.COMMENT|Permission.WRITE_ARTICLES|
				Permission.MODERATE_COMMENTS,False),
			'Administrator':(0xff,False)
		}
		for r in roles:
			role = Role.query.filter_by(name=r).first()
			if role is None:
				role = Role(name=r)
			role.permissions = roles[r][0]
			role.default = roles[r][1]
			db.session.add(role)
		db.session.commit()

	def __repr__(self):
		return '<Role %r>' % self.name

class Post(db.Model):
	__tablename__ = 'posts'
	id = db.Column(db.Integer,primary_key=True)
	body = db.Column(db.Text())
	timestamp = db.Column(db.DateTime(),default=datetime.utcnow,index=True)
	author_id=db.Column(db.Integer,db.ForeignKey('users.id'))
	body_html=db.Column(db.Text())
	comments = db.relationship('Comment',backref='post',lazy='dynamic')

	@staticmethod
	def generate_fake(count=100):
		from random import seed,randint
		import forgery_py

		seed()
		user_count = User.query.count()
		for i in range(count):
			u = User.query.offset(randint(0,user_count-1)).first()
			p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1,3)),
				timestamp=forgery_py.date.date(True),
				author=u)
			db.session.add(p)
			db.session.commit()

	@staticmethod
	def on_change_body(target,value,oldvalue,initiator):
		allowed_tags = ['a','abr','acronym','b','blockquote','code',
		'em','i','li','ol','pre','strong','ul','h1','h2','h3','h4','p']
		target.body_html = bleach.linkify(bleach.clean(markdown(value,output_format='html'),
			tags=allowed_tags,strip=True))
db.event.listen(Post.body,'set',Post.on_change_body )

class Comment(db.Model):
	__tablename__='comments'
	id = db.Column(db.Integer,primary_key=True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
	disabled=db.Column(db.Boolean)
	author_id=db.Column(db.Integer,db.ForeignKey('users.id'))
	post_id = db.Column(db.Integer,db.ForeignKey('posts.id'))
	@staticmethod
	def on_change_body(target,value,oldvalue,initiator):
		allowed_tags = ['a','abr','acronym','b','blockquote','code',
		'em','i','li','ol','pre','strong','ul','h1','h2','h3','h4','p']
		target.body_html = bleach.linkify(bleach.clean(markdown(value,output_format='html'),
			tags=allowed_tags,strip=True))
db.event.listen(Comment.body,'set',Comment.on_change_body )