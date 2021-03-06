#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

migrate = Migrate(app, db)

from models import *


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  areas = Venue.query.with_entities(Venue.city, Venue.state).distinct().order_by(Venue.city, Venue.state).all()
  
  datas = []
  for area in areas:
    area_dic = {}
    area_dic['city'] = area[0]
    area_dic['state'] = area[1]
    area_dic['venues'] = []
    for venue_data in Venue.query.filter_by(city=area[0]).filter_by(state=area[1]).all():
      
      # use join to get both artist and show data
      upcoming_shows = db.session.query(Artist, Show).join(Show).join(Venue).filter(
        Show.venue_id == venue_data.id,
        Show.artist_id == Artist.id,
        Show.start_time > datetime.today()
      ).all()
      venues_data = {
        'id': venue_data.id,
        'name': venue_data.name,
        'num_upcoming_shows': len(upcoming_shows)
      }
      area_dic['venues'].append(venues_data)
    datas.append(area_dic)

  return render_template('pages/venues.html', areas=datas)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  looking_for = '%{0}%'.format(request.form.get('search_term', ''))
  venues = Venue.query.filter(Venue.name.ilike(looking_for)).all()
 
  response = {}
  response["count"] = len(venues)
  response["data"] = []

  for venue in venues:
    upcoming_shows = db.session.query(Artist, Show).join(Show).join(Venue).filter(
      Show.venue_id == venue.id,
      Show.artist_id == Artist.id,
      Show.start_time > datetime.today()
    ).all()
    venue_data = {
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(upcoming_shows)
    }
    response["data"].append(venue_data)

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  venue = Venue.query.filter_by(id=venue_id).first_or_404()

  now = datetime.today()

  past_shows = db.session.query(Artist, Show).join(Show).join(Venue).filter(
    Show.venue_id == venue_id,
    Show.artist_id == Artist.id,
    Show.start_time < now
  ).all()


  upcoming_shows = db.session.query(Artist, Show).join(Show).join(Venue).filter(
    Show.venue_id == venue_id,
    Show.artist_id == Artist.id,
    Show.start_time > now
  ).all()

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": [{
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S.%f")
    } for artist, show in past_shows],
    "upcoming_shows": [{
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S.%f")
    } for artist, show in upcoming_shows],
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False

  try:
    venue = Venue(
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      address = request.form['address'],
      phone = request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      website_link = request.form['website_link'],
      seeking_talent = True if request.form.get('seeking_venue')=='y' else False,
      seeking_description = request.form['seeking_description'],
      genres = request.form.getlist('genres')
    )

    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()

  # on successful db insert, flash success
  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  else:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  venue = Venue.query.get_or_404(venue_id)
  error = False

  try:
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()

  if not error:
    flash("Venue was deleted.")
    return render_template('pages/home.html')
  else:
    flash("An error occured. Venue was not deleted.")
    return render_template('pages/home.html')


  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.all()
  
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  looking_for = '%{0}%'.format(request.form.get('search_term', ''))
  artists = Artist.query.filter(Artist.name.ilike(looking_for)).all()

  response = {}
  response["count"] = len(artists)
  response["data"] = []

  for artist in artists:
    upcoming_shows = db.session.query(Venue, Show).join(Show).join(Artist).filter(
        Show.venue_id == Venue.id,
        Show.artist_id == artist.id,
        Show.start_time > datetime.today()
    ).all()
    artist_data = {
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(upcoming_shows)
    }
    response["data"].append(artist_data)


  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  
  artist = Artist.query.filter_by(id=artist_id).first_or_404()

  now = datetime.today()

  past_shows = db.session.query(Venue, Show).join(Show).join(Artist).filter(
    Show.venue_id == Venue.id,
    Show.artist_id == artist_id,
    Show.start_time < now 
  ).all()

  upcoming_shows = db.session.query(Venue, Show).join(Show).join(Artist).filter(
    Show.venue_id == Venue.id,
    Show.artist_id == artist_id,
    Show.start_time > now
  ).all()

  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": [{
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S.%f")
    } for venue, show in past_shows],
    "upcoming_shows": [{
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S.%f")
    } for venue, show in upcoming_shows],
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  
  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  form = ArtistForm(obj = artist)

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False

  try:
    artist = Artist.query.first_or_404(artist_id)
    form = ArtistForm(request.form)

    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
    artist.website_link = form.website_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data
    artist.genres = form.genres.data

    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()

  if not error:
    return redirect(url_for('show_artist', artist_id=artist_id))
  else:
    flash("An error occurred. Artist was not updated.")
    return render_template('pages/home.html')


  

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  venue = Venue.query.filter_by(id=venue_id).first_or_404()
  form = VenueForm(obj=venue)

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes

  error = False

  try:
    venue = Venue.query.first_or_404(venue_id)
    form = VenueForm(request.form)
    
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data
    venue.website_link = form.website_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data
    venue.genres = form.genres.data
    
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()

  if not error:
    return redirect(url_for('show_venue', venue_id=venue_id))
  else:
    flash("An error occurred. Venue was not updated.")
    #print(sys.exc_info())
    return render_template('pages/home.html')

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  
  try:
    artist = Artist(
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      phone = request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      website_link = request.form['website_link'],
      seeking_venue = True if request.form.get('seeking_venue')=='y' else False,
      seeking_description = request.form['seeking_description'],
      genres = request.form.getlist('genres')
    )

    db.session.add(artist)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  

  # on successful db insert, flash success
  if not error:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  else:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  
  shows = db.session.query(Show).order_by(Show.start_time).all()

  data = [{
    "venue_id": show.venues.id,
    "venue_name": show.venues.name,
    "artist_id": show.artists.id,
    "artist_name": show.artists.name,
    "artist_image_link": show.artists.image_link,
    "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S.%f")
  } for show in shows]
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  error = False
  # next to implement shows create method!
  
  try:
    show = Show(
      artist_id = request.form['artist_id'],
      venue_id = request.form['venue_id'],
      start_time = request.form['start_time']
    )
    db.session.add(show)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()

  if not error:
    flash('Show was successfully listed!')
  else:
    flash('An error occurred. Show could not be listed.')


  # on successful db insert, flash success
  #flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
