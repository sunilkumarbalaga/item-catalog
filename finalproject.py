from flask import Flask, render_template
from flask import request, redirect, jsonify, url_for, flash

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Theatre, Base, MovieName, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from functools import wraps

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Theatres Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///theatres.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# create a state token to request forgery.
# store it in the session for later validation


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_name' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(100))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is  connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if a user exists, if it doesn't make a new one

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 250px; height: 250px;\
    -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    session = DBSession()
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    session.close()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        del login_session['gplus_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        session.close()
        # Reset the user's sesson.
        return redirect(url_for('showtheatre'))
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/logout')
def logout():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            flash("you have succesfully been logout")
        return redirect(url_for('showtheatre'))
    else:
        flash("you were not logged in")
        return redirect(url_for('showtheatre'))


# JSON APIs to view theatre Information
@app.route('/theatre/<int:theatre_id>/movie/JSON')
def theatreinfoJSON(theatre_id):
    session = DBSession()
    theatre = session.query(Theatre).filter_by(id=theatre_id).one()
    movies = session.query(MovieName).filter_by(
        theatre_id=theatre_id).all()
    session.close()
    return jsonify(MovieNames=[i.serialize for i in movies])


@app.route('/theatre/<int:theatre_id>/movie/<int:movie_id>/JSON')
def MovieinfoJSON(theatre_id, movie_id):
    session = DBSession()
    Movie_Name = session.query(MovieName).filter_by(id=movie_id).one()
    session.close()
    return jsonify(Movie_Name=Movie_Name.serialize)


@app.route('/theatre/JSON')
def theatresJSON():
    session = DBSession()
    theatre = session.query(Theatre).all()
    session.close()
    return jsonify(theatre=[r.serialize for r in theatres])


# Show all theatres
@app.route('/')
@app.route('/theatre/')
def showtheatre():
    session = DBSession()
    theatre= session.query(Theatre).all()
    session.close()
    return render_template('theatre.html', theatre=theatre)

@app.route('/theatre/<int:theatre_id>')
def theatreinfo(theatre_id):
    session = DBSession()
    theatre = session.query(Theatre).filter_by(id=theatre_id).one()
    movies = session.query(MovieName).filter_by(
        theatre_id=theatre_id).all()
    session.close()
    return render_template('movie.html', theatre=theatre, movies=movies)


@app.route('/theatre/<int:theatre_id>/movie/<int:movie_id>')
def movieinfo(theatre_id, movie_id):
    session = DBSession()
    Movie_Name = session.query(MovieName).filter_by(id=movie_id).one()
    session.close()
    return jsonify(Movie_Name=Movie_Name.serialize)
# Create a new theatre


@app.route('/theatre/new/', methods=['GET', 'POST'])
def newtheatre():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        session = DBSession()
        newtheatre = Theatre(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newtheatre)
        flash('New theatre %s Successfully Created' % newtheatre.name)
        session.commit()
        session.close()
        return redirect(url_for('showtheatre'))
    else:
        return render_template('newtheatre.html')

# Edit a theatre


@app.route('/theatre/<int:theatre_id>/edit/', methods=['GET', 'POST'])
def edittheatre(theatre_id):
    if 'username' not in login_session:
        return redirect('/login')
    session = DBSession()
    editedtheatre = session.query(
       Theatre).filter_by(id=theatre_id).one()
    creator = getUserInfo(editedtheatre.user_id)
    user = getUserInfo(login_session['user_id'])
    print creator.id
    print login_session['user_id']
    if creator.id != login_session['user_id']:
        flash("You cannot edit this theatre. This theatre belongs to % s"
              % creator.name)
        return redirect(url_for('showtheatre'))
    if request.method == 'POST':
        if request.form['name']:
            editedtheatre.name = request.form['name']
            flash('theatre Successfully Edited %s' % editedtheatre.name)
            session.commit()
            session.close()
            return redirect(url_for('showtheatre'))
    else:
        return render_template('edittheatre.html',theatre=editedtheatre)


# Delete a theatre
@app.route('/theatre/<int:theatre_id>/delete/', methods=['GET', 'POST'])
def deletetheatre(theatre_id):
    if 'username' not in login_session:
        return redirect('/login')
    session = DBSession()
    theatreToDelete = session.query(
       Theatre).filter_by(id=theatre_id).one()
    creator = getUserInfo(theatreToDelete.user_id)
    user = getUserInfo(login_session['user_id'])
    if creator.id != login_session['user_id']:
        flash("You cannot delete this theatre. This theatre belongs to %s"
              % creator.name)
        return redirect(url_for('showtheatre'))
    if request.method == 'POST':
        session.delete(theatreToDelete)
        flash('%s Successfully Deleted' % theatreToDelete.name)
        session.commit()
        session.close()
        return redirect(url_for('showtheatre', theatre_id=theatre_id))
    else:
        return render_template('deleteTheatre.html', theatre=theatreToDelete)

# Show a theatremovies


@app.route('/theatre/<int:theatre_id>/')
@app.route('/theatre/<int:theatre_id>/movie/')
def showMovies(theatre_id):
    session = DBSession()
    theatre = session.query(Theatre).filter_by(id=theatre_id).one()
    movies = session.query(MovieName).filter_by(
        theatre_id=theatre_id).all()
    session.close()
    return render_template('movie.html', movies=movies, theatre=theatre)


# Create a new movie
@app.route('/theatre/<int:theatre_id>/movie/new/', methods=['GET', 'POST'])
def newmovieName(theatre_id):
    if 'username' not in login_session:
        return redirect('/login')
    session = DBSession()
    theatre = session.query(Theatre).filter_by(id=theatre_id).one()
    if request.method == 'POST':
        newmovie = MovieName(name=request.form['name'],
                               description=request.form['description'],
                               fee=request.form['fee'],
                               theatre_id=theatre_id, user_id=theatre.user_id)
        session.add(newmovie)
        session.commit()
        flash('New Movie %s Name Successfully Created' % (newmovie.name))
        session.close()
        return redirect(url_for('showMovies', theatre_id=theatre_id))
    else:
        return render_template('newMovieName.html', theatre_id=theatre_id)

# Edit a movie


@app.route('/theatre/<int:theatre_id>/movie/<int:movie_id>/edit',
           methods=['GET', 'POST'])
def editMovieName(theatre_id, movie_id):
    session = DBSession()
    if 'username' not in login_session:
        return redirect('/login')
    
    editedMovie = session.query(MovieName).filter_by(id=movie_id).one()
    theatre = session.query(Theatre).filter_by(id=theatre_id).one()
    creator = getUserInfo(editedMovie.user_id)
    user = getUserInfo(login_session['user_id'])
    if creator.id != login_session['user_id']:
        flash("You cannot edit this theatre. This theatre belongs to %s"
              % creator.name)
        return redirect(url_for('showMovies'))
    if request.method == 'POST':
        if request.form['name']:
            editedMovie.name = request.form['name']
        if request.form['description']:
            editedMovie.description = request.form['description']
        if request.form['fee']:
            editedMovie.fee = request.form['fee']
        session.add(editedMovie)
        session.commit()
        flash('Movie Name Successfully Edited')
        session.close()
        return redirect(url_for('showMovies', theatre_id=theatre_id))
    else:
        return render_template('editMovieName.html',
                               theatre_id=theatre_id, movie_id=movie_id,
                               movie=editedMovie)


# Delete a course
@app.route('/theatre/<int:theatre_id>/movie/<int:movie_id>/delete',
           methods=['GET', 'POST'])
def deleteMovieName(theatre_id, movie_id):
    session = DBSession()
    if 'username' not in login_session:
        return redirect('/login')
    session = DBSession()
    theatre = session.query(Theatre).filter_by(id=theatre_id).one()
    movieToDelete = session.query(MovieName).filter_by(id=movie_id).one()
    creator = getUserInfo(movieToDelete.user_id)
    user = getUserInfo(login_session['user_id'])
    if creator.id != login_session['user_id']:
        flash("You cannot delete this theatre. This theatre belongs to %s"
              % creator.name)
        return redirect(url_for('showMovies'))
    if request.method == 'POST':
        session.delete(movieToDelete)
        session.commit()
        flash('Movie Name Successfully Deleted')
        session.close()        
	return redirect(url_for('showMovies',theatre_id=theatre_id))
    else:
        return render_template('deleteMovieName.html', movie=movieToDelete)


session.close()
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
