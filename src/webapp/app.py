from flask import Flask, render_template
from flask_apscheduler import APScheduler
import jobs

app = Flask(__name__)
scheduler = APScheduler()

@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/covid-19-viz/')
def get_covid_viz():
    return render_template('COVID-19_viz.html')

@app.route('/gdp-viz/')
def get_gdp_viz():
    return render_template('GDP_viz.html')

@app.route('/sf-crime-viz/')
def get_crime_viz():
    return render_template('SF_crime_viz.html')

@app.route('/uk-accidents-viz/')
def get_accidents_viz():
    return render_template('UK_accidents_viz.html')

if __name__ == '__main__':
    jobs.create_all()
    scheduler.add_job(id='Covid-19 data update', func=jobs.covid_update, trigger='cron', hour=6, minute=30)
    scheduler.add_job(id='SF crime data update', func=jobs.sf_crime_update, trigger='cron', hour=19, minute=15)
    scheduler.start()
    app.run()