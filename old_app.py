from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import io
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///steel_production.db'
db = SQLAlchemy(app)

# Database models
class DailyCharge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    mould_size = db.Column(db.String(50))

class ProductGroupForecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quality = db.Column(db.String(50), nullable=False)
    month = db.Column(db.Date, nullable=False)
    heats = db.Column(db.Integer, nullable=False)

class SteelGradeProduction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quality_group = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    month = db.Column(db.Date, nullable=False)
    production = db.Column(db.Float, nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload/<file_type>', methods=['POST'])
def upload_file(file_type):
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file_type == 'daily_charge':
        return upload_daily_charge(file)
    elif file_type == 'product_groups':
        return upload_product_groups(file)
    elif file_type == 'steel_grade_production':
        return upload_steel_grade_production(file)
    else:
        return jsonify({"error": "Invalid file type"}), 400

def upload_daily_charge(file):
    if not file:
        return jsonify({"error": "No file provided"}), 400

    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.reader(stream)
    
    # Skip the "Daily charge schedule" header
    next(csv_input)
    
    # Read the date row
    date_row = next(csv_input)
    dates = [date for date in date_row if date.strip()]
    
    # Read the column headers
    headers = next(csv_input)
    
    # Process data rows
    for row in csv_input:
        if len(row) == 0 or all(cell == '' for cell in row):
            continue  # Skip empty rows
        
        start_time = row[0]
        for i, (grade, mould_size) in enumerate(zip(row[1::3], row[2::3])):
            if grade and grade != '-':
                try:
                    date = datetime.strptime(dates[i//3], '%A %m/%d/%Y').date()
                    time = datetime.strptime(start_time, '%H:%M').time()
                    
                    charge = DailyCharge(
                        date=date,
                        start_time=time,
                        grade=grade,
                        mould_size=mould_size if mould_size != '-' else None
                    )
                    db.session.add(charge)
                except ValueError as e:
                    return jsonify({"error": f"Error parsing row: {row}. {str(e)}"}), 400
                except IndexError:
                    return jsonify({"error": f"Mismatched data in row: {row}"}), 400

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({"message": "Daily charge schedule uploaded successfully"}), 200

def upload_product_groups(file):
    if not file:
        return jsonify({"error": "No file provided"}), 400

    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.reader(stream)
    next(csv_input)  # Skip header row
    next(csv_input)  # Skip column names row

    for row in csv_input:
        if len(row) >= 5:
            quality = row[0]
            for i, month in enumerate(['Jun 24', 'Jul 24', 'Aug 24', 'Sep 24']):
                heats = int(row[i+1]) if row[i+1] else 0
                date = datetime.strptime(f"01 {month}", '%d %b %y').date()
                forecast = ProductGroupForecast(quality=quality, month=date, heats=heats)
                db.session.add(forecast)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({"message": "Product groups forecast uploaded successfully"}), 200

def upload_steel_grade_production(file):
    if not file:
        return jsonify({"error": "No file provided"}), 400

    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.reader(stream)
    next(csv_input)  # Skip header row
    next(csv_input)  # Skip column names row

    current_quality_group = None
    for row in csv_input:
        if len(row) >= 5:
            if row[0]:
                current_quality_group = row[0]
            grade = row[1]
            for i, month in enumerate(['Jun 24', 'Jul 24', 'Aug 24']):
                production = float(row[i+2]) if row[i+2] else 0
                date = datetime.strptime(f"01 {month}", '%d %b %y').date()
                production_record = SteelGradeProduction(
                    quality_group=current_quality_group,
                    grade=grade,
                    month=date,
                    production=production
                )
                db.session.add(production_record)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({"message": "Steel grade production history uploaded successfully"}), 200


@app.route('/forecast/september', methods=['GET'])
def forecast_september():
    # Get the September product group forecast
    september = datetime(2024, 9, 1).date()
    group_forecast = ProductGroupForecast.query.filter_by(month=september).all()
    
    # Get the most recent month's production data (August)
    august = datetime(2024, 8, 1).date()
    production_history = SteelGradeProduction.query.filter_by(month=august).all()
    
    # Calculate grade percentages within each product group
    group_percentages = {}
    for prod in production_history:
        if prod.quality_group not in group_percentages:
            group_percentages[prod.quality_group] = {}
        group_total = sum([p.production for p in production_history if p.quality_group == prod.quality_group])
        if group_total > 0:
            group_percentages[prod.quality_group][prod.grade] = prod.production / group_total
    
    # Calculate September forecast
    forecast = {}
    for group in group_forecast:
        if group.quality in group_percentages:
            for grade, percentage in group_percentages[group.quality].items():
                forecast_heats = round(group.heats * percentage)
                if forecast_heats > 0:
                    forecast[grade] = forecast_heats
    
    return jsonify(forecast)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
