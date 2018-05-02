# Created by Megan Shum
# CS304-Final project
# 2018.04.27
#!/usr/local/bin/python2.7

from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug import secure_filename
app = Flask(__name__)

import bcrypt
import sys,os,random
import dbconn2
import profops
import imghdr
import time
import uploadops
import accounts
import newsfeedOps
import searchops


app.secret_key = 'your secret here'
# replace that with a random key
app.secret_key = ''.join([ random.choice(('ABCDEFGHIJKLMNOPQRSTUVXYZ' +
                                          'abcdefghijklmnopqrstuvxyz' +
                                          '0123456789'))
                           for i in range(20) ])

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

# Process login form
@app.route('/', methods=['GET', 'POST'])
def loginProcess():
	# When get, return empty login page
    if request.method == 'GET':
        if 'username' in session:
            return redirect(url_for('newsfeed'))
        return render_template('login.html',
    							title='Login')
    else:
        username = request.form['username']
        passwd = request.form['passwd']
        conn = dbconn2.connect(DSN)
    	# If valid username and password
        if (accounts.validUsername(conn, username)):
            storedHash = accounts.getHashedPassword(conn, username)
            if(bcrypt.hashpw(passwd.encode('utf-8'), storedHash.encode('utf-8')) == storedHash.encode('utf-8')):
				# Save username to the session
				session['username'] = username
				return redirect(url_for('newsfeed'))
            else:
                flash("Login failed. Please try again")
                return render_template('login.html',
            							title='Login')
        else:
            flash("Invalid username. Please try again")
            return render_template('login.html',
                                    title='Login')

@app.route('/logout/')
def logout():
    session.pop('username', None)
    return redirect(url_for('loginProcess'))

@app.route('/register/')
def register():
	return render_template('register.html',
							title='Register',
							script=url_for('registerProcess'))

# Process login form
@app.route('/register/', methods=['POST'])
def registerProcess():
	# When get, return empty login page
	if request.method == 'GET':
		flash("Registration failed. Please try again")
		return register()
	else:
		name = request.form['name']
		email = request.form['email']
		username = request.form['username']
		passwd = request.form['passwd']
		comPasswd = request.form['comPasswd']
        print(name)
        if((name == "") or (email == "") or (username == "") or (passwd == "") or (comPasswd == "")):
            flash("Please fill out all fields")
            return register()
    	conn = dbconn2.connect(DSN)
    	if (accounts.validUsername(conn, username)):
    		flash("Username is taken")
    		return register()
    	if (passwd != comPasswd):
    		flash("Passwords do not match")
    		return register()
    	# Register new account
    	hashed = bcrypt.hashpw(passwd.encode('utf-8'), bcrypt.gensalt())
    	# If valid username and password
    	accounts.registerUser(conn, username, hashed, name, email)
    	flash("Registration successful")
    	return redirect(url_for('loginProcess'))

@app.route('/upload/', methods = ['GET', 'POST'])
def upload():
    if not session['username']: #I am assuming Maxine will create the cookie once the user logs in
         flash("Please login")
         return redirect(url_for('loginProcess')) # i am assuming that Maxine will make this route
    else:
        if request.method == 'GET':
            return render_template('upload.html')
        else:
            try:
                username = session['username']
                description = request.form['description'] # may throw error
                location = request.form['location']
                time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
                f = request.files['pic']
                mime_type = imghdr.what(f.stream)
                if mime_type != 'jpeg':
                    raise Exception('Not a JPEG')
                pic = secure_filename(str(f.filename))
                pathname = 'images/'+ pic
                f.save(pathname) # saves the contents in a temporarily in the images folder
                flash('Upload successful')
                conn = dbconn2.connect(DSN)
                uploadops.uploadPost(conn, username, description, location,         time_stamp, pic)
                return render_template('upload.html',
                                       src=url_for('pic',fname=pic)
                                       )
            except Exception as err:
                flash('Upload failed {why}'.format(why=err))
                return render_template('upload.html')

@app.route('/profile/<username>', methods = ['GET'])
def profile(username):
    if not session['username']:
         flash("Please log in")
         return redirect(url_for('loginProcess'))
    else:
        if request.method == 'GET':
            conn = dbconn2.connect(DSN)
            followers = profops.getFollow(conn, username)
            following = profops.getFollowing(conn, username)
            pics = profops.retrievePics(conn, username)
            return render_template('profile.html',
                                    username = username,
                                    followers = followers,
                                    following = following,
                                    pics = pics
                                    )
@app.route('/toUserProfile/')
def toUserProfile():
    if session['username']:
        return redirect(url_for('profile', username = session['username']))
    else:
        flash("Please login")
        return redirect(url_for('loginProcess'))

@app.route('/search/', methods = ["POST"])
def search():
    if request.method == "POST":
        search = request.form['search']
        if search == "":
            flash('Please enter a username')
            return redirect(url_for('newsfeed'))
        else:
            conn = dbconn2.connect(DSN)
            if searchops.searchExists(conn, search):
                return redirect(url_for('profile', username = search))
            else:
                flash('User does not exist')
                return redirect(url_for('newsfeed'))


@app.route('/newsfeed/', methods = ['GET','POST'])
def newsfeed():
    if session['username']:
        username = session['username']
        conn = dbconn2.connect(DSN)
        information = newsfeedOps.retrievePics(conn, username)
        if (information != None):
            return render_template ('newsfeed.html',username = username, posts = information)
        else:
            flash("Follow people to see pictures on your Newsfeed!")
            return render_template('newsfeed.html', username = username, posts = None)
    else:
         return redirect (url_for (''))

# renders images
@app.route('/images/<fname>')
def pic(fname):
    f = secure_filename(fname)
    mime_type = f.split('.')[-1]
    val = send_from_directory('images',f)
    return val

if __name__ == '__main__':

    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert(port>1024)
    else:
        port = os.getuid()
    DSN = dbconn2.read_cnf()
    DSN['db'] = 'mmm_db'
    app.debug = True
    app.run('0.0.0.0',port)
