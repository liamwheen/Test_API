from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.utils import secure_filename
from predict_sept import predict, calc_interval, plot_prediction
import os
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///steel_production.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'key'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

class DailyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    mould_size = db.Column(db.String(50), nullable=False)

class MonthlyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Date, nullable=False)
    quality_group = db.Column(db.String(50), nullable=False)
    heats = db.Column(db.Integer, nullable=False)

class SteelGradeProduction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Date, nullable=False)
    quality_group = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(50), nullable=True)
    production = db.Column(db.Float, nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_daily', methods=['GET', 'POST'])
def upload_daily():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                logger.info(f"File saved to {file_path}")
                process_daily_plan(file_path)
                flash('File uploaded and processed successfully')
                return redirect(url_for('index'))
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}", exc_info=True)
                flash(f'An error occurred: {str(e)}')
                return redirect(request.url)
    return render_template('upload_daily.html')

def process_daily_plan(file_path):
    logger.info(f"Processing daily plan file: {file_path}")

    try:
        # Read the CSV file
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Extract dates from the header (second row)
        header_line = lines[1].strip()
        header_parts = [part.strip() for part in header_line.split(',')]
        
        # Extract the dates (assuming every 3 columns represent a new day's data)
        dates = []
        for part in header_parts:
            if '/' in part:
                try:
                    dates.append(pd.to_datetime(part).date())
                    logger.debug(f"Found date: {dates[-1]}")
                except ValueError:
                    logger.warning(f"Invalid date format: {part}")

        # Initialize data storage for each date
        daily_data = {date: [] for date in dates}

        # Process the lines starting from the third row (skip the first two rows)
        for line in lines[2:]:
            line = line.strip()
            if not line:
                continue

            parts = [part.strip() for part in line.split(',')]
            
            # Each row contains three sets of start_time, grade, and mould_size for different dates
            for i in range(len(dates)):
                start_idx = i * 3  # Each set consists of 3 fields (start_time, grade, mould_size)
                if len(parts) >= start_idx + 3:
                    start_time = parts[start_idx] if parts[start_idx] else None
                    grade = parts[start_idx + 1] if parts[start_idx + 1] else None
                    mould_size = parts[start_idx + 2] if parts[start_idx + 2] else None

                    if start_time and grade:  # Only store if there's a valid start_time and grade
                        daily_data[dates[i]].append({
                            'start_time': start_time,
                            'grade': grade,
                            'mould_size': mould_size
                        })

        # Now process the data day by day
        for date in dates:
            for entry in daily_data[date]:
                try:
                    start_time_obj = pd.to_datetime(entry['start_time']).time()
                    daily_plan = DailyPlan(
                        date=date,
                        start_time=start_time_obj,
                        grade=entry['grade'],
                        mould_size=entry['mould_size']
                    )
                    db.session.add(daily_plan)
                    logger.debug(f"Added plan: {date}, {start_time_obj}, {entry['grade']}, {entry['mould_size']}")
                except Exception as e:
                    logger.error(f"Error processing entry for {date}: {str(e)}")
        
        db.session.commit()
        logger.info("Daily plan processing completed successfully")
    
    except Exception as e:
        logger.error(f"Error in process_daily_plan: {str(e)}", exc_info=True)
        raise

@app.route('/upload_monthly', methods=['GET', 'POST'])
def upload_monthly():
    if request.method == 'POST':
        # Check for required files
        if 'monthly_file' not in request.files or 'steel_grade_file' not in request.files:
            flash('Both files are required')
            return redirect(request.url)
        
        monthly_file = request.files['monthly_file']
        steel_grade_file = request.files['steel_grade_file']
        
        # Check if filenames are empty
        if monthly_file.filename == '' or steel_grade_file.filename == '':
            flash('Both files must be selected')
            return redirect(request.url)
        
        if monthly_file and steel_grade_file:
            try:
                # Save monthly file
                monthly_filename = secure_filename(monthly_file.filename)
                monthly_file_path = os.path.join(app.config['UPLOAD_FOLDER'], monthly_filename)
                monthly_file.save(monthly_file_path)
                logger.info(f"Monthly file saved to {monthly_file_path}")
                
                # Save steel grade file
                steel_grade_filename = secure_filename(steel_grade_file.filename)
                steel_grade_file_path = os.path.join(app.config['UPLOAD_FOLDER'], steel_grade_filename)
                steel_grade_file.save(steel_grade_file_path)
                logger.info(f"Steel grade production file saved to {steel_grade_file_path}")

                # Process both files
                process_monthly_plan(monthly_file_path)
                process_steel_grade_production(steel_grade_file_path)
                
                flash('Both files uploaded and processed successfully')
                return redirect(url_for('upload_monthly'))
            except Exception as e:
                logger.error(f"Error processing files: {str(e)}", exc_info=True)
                flash(f'An error occurred: {str(e)}')
                return redirect(request.url)

    return render_template('upload_monthly.html')

def process_monthly_plan(file_path):
    df = pd.read_csv(file_path, skiprows=1)
    for _, row in df.iterrows():
        for month in ['Jun 24', 'Jul 24', 'Aug 24', 'Sep 24']:
            if month in row and pd.notna(row[month]):
                monthly_plan = MonthlyPlan(
                    month=pd.to_datetime(month, format='%b %y').date(),
                    quality_group=row['Quality:'],
                    heats=row[month])
                db.session.add(monthly_plan)
    db.session.commit()

def process_steel_grade_production(file_path):
    logger.info(f"Processing steel grade production file: {file_path}")
    try:
        # Read CSV, skipping the first row
        df = pd.read_csv(file_path, skiprows=1)
        logger.debug(f"DataFrame shape: {df.shape}")
        logger.debug(f"DataFrame columns: {df.columns}")
        logger.debug(f"First few rows:\n{df.head()}")

        current_quality_group = None  # Variable to hold the last valid quality group
        
        for _, row in df.iterrows():
            quality_group = row['Quality group']
            grade = row['Grade']
            
            # Update quality group if the current row has a valid one
            if pd.notna(quality_group): 
                current_quality_group = quality_group
            
            # Process each month (June, July, August) for production data
            for month in ['Jun 24', 'Jul 24', 'Aug 24']:
                if month in row.index and pd.notna(row[month]):
                    try:
                        production = SteelGradeProduction(
                            month=pd.to_datetime(month, format='%b %y').date(),
                            quality_group=current_quality_group,
                            grade=grade if pd.notna(grade) else 'Unknown',  # Set default for missing grades
                            production=float(row[month])  # Convert production to float
                        )
                        db.session.add(production)
                        logger.debug(f"Added production: {month}, {current_quality_group}, {grade}, {row[month]}")
                    except Exception as e:
                        logger.error(f"Error adding production for {grade}: {str(e)}")
        
        db.session.commit()  # Commit changes to the database
        logger.info("Steel grade production processing completed successfully")

    except Exception as e:
        db.session.rollback()  # Rollback in case of an error
        logger.error(f"Error in process_steel_grade_production: {str(e)}", exc_info=True)
        raise

def generate_prediction_data(db):
    query_production = text("SELECT * FROM steel_grade_production")
    query_monthly = text("SELECT quality_group, heats FROM monthly_plan")
    
    with db.engine.connect() as connection:
        production_data = connection.execute(query_production)
        quality_arrays = {}
        grade_data = {}
        for row in production_data:
            print(row)
            quality_group, grade, production = row[2:5]
            quality_arrays.setdefault(quality_group, []).append(production)
            grade_data.setdefault(quality_group, []).append(grade)

        # Save just the unique grades for each quality group (in order)
        for group in grade_data.keys():
            grade_data[group] = list(dict.fromkeys(grade_data[group]))
        quality_arrays = {quality: np.array(values).reshape(-1, 3) for quality, values in quality_arrays.items()}
        
        monthly_data = {row[0]: row[1] for row in connection.execute(query_monthly)}
    
    return quality_arrays, monthly_data, grade_data

@app.route('/predict_september', methods=['GET', 'POST'])
def predict_september():
    try:
        quality_arrays, monthly_data, grade_data = generate_prediction_data(db)
        
        predictions = []
        for quality, data in quality_arrays.items():
            prediction = predict(data, monthly_data[quality] * 100)[:-1, -1]
            interval_data = calc_interval(data, monthly_data[quality] * 100)[:, 1:]
            predictions.append({
                'quality': quality,
                'grades': grade_data[quality],
                'prediction': [f"{value:.2f}" for value in prediction],
                'confidence': [[f"{conf[0]:.2f}", f"{conf[1]:.2f}"] for conf in interval_data]
            })
        
        return render_template('prediction_table.html', predictions=predictions)
    except Exception as e:
        logger.error(f"Error in predict_september: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/get_plot/<quality>', methods=['GET'])
def get_plot(quality):
    try:
        quality_arrays, monthly_data, _ = generate_prediction_data(db)
        
        if quality not in quality_arrays:
            return jsonify({'error': 'Quality not found'}), 404
        
        data = quality_arrays[quality]
        tot = monthly_data[quality] * 100
        
        plot_url = plot_prediction(data, tot)
        
        return jsonify({'plot_url': plot_url})
    except Exception as e:
        logger.error(f"Error in get_plot: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
