from flask import Flask, render_template, request, url_for, redirect, session, flash
from markupsafe import Markup
import folium
import json
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load GeoJSON data
with open('africa_outline.geojson') as f:
    africa_geojson = json.load(f)

# a list of all african countries from GeoJSON
african_countries = [feature['properties']['name'].title() for feature in africa_geojson['features']]


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'guessed_countries' not in session:
        session['guessed_countries'] = []

    guessed_countries = session['guessed_countries']

    if request.method == 'POST':
        guessed_country = request.form['country'].strip().title()

        # Check if the guessed country exists in the african_countries (GeoJSON file)
        if guessed_country in african_countries and guessed_country not in guessed_countries:
            guessed_countries.append(guessed_country)
            session['guessed_countries'] = guessed_countries
        else:
            flash("Invalid guess or Country already guessed.", "error")

        if len(guessed_countries) == len(african_countries):
            flash("Congratulations! You've guessed all the countries!", "success")

        return redirect(url_for('index'))

    # Folium map centered on Africa without tile layers
    m = folium.Map(location=[0, 20], zoom_start=3, tiles=None)

    # Add the GeoJSON layer to the map
    for feature in africa_geojson['features']:
        country_name = feature['properties']['name'].title()
        coordinates = feature['geometry']['coordinates']
        if feature['geometry']['type'] == 'Polygon':
            marker_location = coordinates[0][0]
        elif feature['geometry']['type'] == 'MultiPolygon':
            marker_location = coordinates[0][0][0]
        else:
            continue

        style_function = {
            'fillColor': 'transparent',
            'color': 'black',
            'weight': 2,
            'opacity': 1,
        }

        # If the country is guessed, change the style to fill the country
        if country_name in guessed_countries:
            style_function['fillColor'] = "green"
            # Add a Marker for the guessed country
            folium.Marker(
                location=[marker_location[1], marker_location[0]],
                popup=country_name,
                icon=folium.Icon(color='blue')
            ).add_to(m)

        # Add each country's GeoJSON
        folium.GeoJson(
            feature,
            style_function=lambda x, style= style_function: style,
            tooltip=feature['properties']['name'] if country_name in guessed_countries else None
        ).add_to(m)

    map_html = m._repr_html_()
    total_africa_country = len(african_countries)
    user_score = len(guessed_countries)

    return render_template('index.html', map_html=Markup(map_html), total=total_africa_country, score=user_score)


@app.route("/corrections")
def correction():
    guessed_countries = session.get('guessed_countries', [])
    return render_template('africa.html', guessed_countries=guessed_countries, total_countries=african_countries)


@app.route('/reset', methods=['POST'])
def reset_session():
    session.clear()  # Clears all session data
    flash("Session has been reset!", "info")  # Optional: Flash message
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
