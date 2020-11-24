#app/views.py


from flask import render_template, flash, redirect, url_for, session,request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField,PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

from app import app
#from data import Articles


app.secret_key='secrect123'

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] ='Autonoma123*'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#INIT MYSQL
mysql = MySQL(app)

class RegisterForm(Form):

	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	email = StringField('Email', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [validators.DataRequired(),validators.EqualTo('confirm', message='Password do not match')])
	confirm = PasswordField('Confirm Password')


@app.route('/')
def index():
	return render_template("index.html")


@app.route('/about')
def about():
	return render_template("about.html")

@app.route('/Articles')
def articles():
	#Create cursor
        cur =  mysql.connection.cursor()
        #get
        result = cur.execute("SELECT * FROM articles")

        articles = cur.fetchall()
        if result > 0 :
                return render_template('Articles.html', articles=articles)

        else:
                msg = 'No Articles found'
                return render_template('Articles.html', msg = msg)
        #close connection
        cur.close()
	

@app.route('/Article/<string:id>/')
def article(id):
        #Create cursor
        cur =  mysql.connection.cursor()
        #get
        result = cur.execute("SELECT * FROM articles WHERE id= %s", [id])

        article = cur.fetchone()
	return render_template('Article.html', article=article)

@app.route('/register',methods=['GET','POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))

		# Create Cursor
		cur = mysql.connection.cursor()
		# Execute Query
		cur.execute("INSERT INTO users(name, email,username, password) VALUES(%s, %s, %s, %s)", (name, email,username,password))
		# Commit to DB
		mysql.connection.commit()
		# Close connection
		cur.close()
		flash('You are now registered and canlog in', 'success')
		
		return redirect(url_for('index'))

	return render_template('register.html',form=form) 
	
#user login
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
	
		# Get Form Fields
		username = request.form['username']
		password_candidate = request.form['password']
		# Create cursor
		cur = mysql.connection.cursor()
		# Get user by username
		result = cur.execute("SELECT * FROM users WHERE username =%s",[username])
		if result > 0:
			# Get stored hash
			data = cur.fetchone()
			password = data['password']

			# Compare Passwords
			if sha256_crypt.verify(password_candidate, password):
				# Passed
				session['logged_in'] = True
				session['username'] = username
				flash('You are logged in', 'success')
				app.logger.info('PASSWORD MATCHED')
				return redirect(url_for('dashboard'))
			else:

				app.logger.info('PASSWORD NO MATCHED')
				error = 'Invalid login'
				return render_template('login.html', error=error)

		# Close connection
			cur.close()
		else:
			app.logger.info('NO USER')
			error = 'Username not found'
			return render_template('login.html', error=error)

	return render_template('login.html')



def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Plese login', 'danger')
			return redirect(url_for('login'))

	return wrap

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
	#Create cursor
	cur =  mysql.connection.cursor()
	#get
	result = cur.execute("SELECT * FROM articles")
	
	articles = cur.fetchall()
	if result > 0:
		return render_template('dashboard.html', articles=articles)
	else:
		msg = 'No Articles found'
		return render_template('dashboard.html', msg = msg)
	#close connection
	cur.close()

#Article form class
class ArticleForm(Form):
	title = StringField('Title',[validators.Length(min=1, max=2000)])
	body = TextAreaField ('Body',[validators.Length(min=30)])

#Add article
@app.route('/add_article',methods = ['GET' , 'POST'])
@is_logged_in
def add_article():
	form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title =  form.title.data
		body  =  form.body.data
		
		#Create Cursor
		cur = mysql.connection.cursor()
		
		#Execute
		cur.execute("INSERT INTO articles(title,body,author) VALUES (%s,%s,%s)",(title,body, session['username']))

		#commit 
		mysql.connection.commit()
		#close
		cur.close()

		flash('Article Created', 'success')

		return redirect(url_for('dashboard'))

	return render_template('add_article.html', form=form) 

# Logout
@app.route('/logout')
def logout():
	session.clear()
	flash('You are now logged out','success')
	return redirect(url_for('login'))

#Edit article
@app.route('/edit_article/<string:id>',methods = ['GET' , 'POST'])
@is_logged_in
def edit_article(id):

	#Create cursor
	cur = mysql.connection.cursor()

	#get article by id
	result =  cur.execute("SELECT * FROM articles WHERE id = %s", [id])

	article = cur.fetchone()
	#get form
        form = ArticleForm(request.form)

	form.title.data = article['title']
	form.body.data = article['body']
	
        if request.method == 'POST' and form.validate():
                title =  request.form['title']
                body  =  request.form['body']

                #Create Cursor
                cur = mysql.connection.cursor()

                #Execute
                cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title,body,id))

                #commit
                mysql.connection.commit()
                #close
                cur.close()

                flash('Article Update', 'success')

                return redirect(url_for('dashboard'))

        return render_template('edit_article.html', form=form)

#Delete article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Execute
	cur.execute("DELETE FROM articles WHERE id = %s", [id])
	
	#Commit to DB
	mysql.connection.commit()
	
	#Close connection
	cur.close()
	
	flash ('Article Deleted','success')

	return redirect(url_for('dashboard'))
