from flask import Flask, render_template, jsonify, request
from schedule import load_workers_from_csv, schedule_shifts, DAYS, SHIFTS
import pandas as pd
import csv
import os
import uuid
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
app.config['UPLOAD_FOLDER'] = '.'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# --- Global State ---
# This is a simple way to store state for this demo.
# For a production app, you would typically use a database.
WORKERS_DATA = load_workers_from_csv('workers.csv')
ALL_WORKERS = list(WORKERS_DATA.keys())
current_schedule = {}
current_assignments = {}

# Store worker availability submissions
WORKER_AVAILABILITY = {}

def convert_preferences_to_scheduler_format(worker_name, available_days, preferences):
    """
    Convert daily preferences from the availability form into the format expected by the scheduler.
    Returns data in the format: {'unavailable': [], 'preferences': [], 'day_off': ''}
    """
    unavailable = []
    preferred = []
    day_off = ''
    
    # Get all possible day-shift combinations
    all_combinations = []
    for day in DAYS:
        for shift in SHIFTS:
            all_combinations.append((day, shift))
    
    # For each day-shift combination, determine if worker is available
    for day, shift in all_combinations:
        if day not in available_days:
            # Worker is not available on this day at all
            unavailable.append((day, shift))
        else:
            # Worker is available, check their preference
            day_prefs = preferences.get(day, {})
            shift_pref = day_prefs.get(shift, 2)  # Default to neutral (2)
            
            if shift_pref == 3:  # Least preferred
                # Add to unavailable (they really don't want this shift)
                unavailable.append((day, shift))
            elif shift_pref == 1:  # Most preferred
                # Add to preferred list
                preferred.append((day, shift))
            # If preference is 2 (neutral), don't add to either list
    
    return {
        'unavailable': unavailable,
        'preferences': preferred,
        'day_off': ''  # No specific day off in this system
    }

def update_workers_csv_from_availability():
    """
    Update the workers.csv file with data from the availability form submissions.
    """
    with open("workers.csv", mode="w", newline="", encoding='utf-8') as file:
        writer = csv.writer(file)
        
        for worker_name, data in WORKER_AVAILABILITY.items():
            available_days = data['available_days']
            preferences = data['preferences']
            
            # Convert to scheduler format
            scheduler_data = convert_preferences_to_scheduler_format(
                worker_name, available_days, preferences
            )
            
            # Format unavailable times
            unavailable_str = ';'.join([f"{day}:{shift}" for day, shift in scheduler_data['unavailable']])
            if not unavailable_str:
                unavailable_str = 'nan'
            
            # Format preferred times
            preferred_str = ';'.join([f"{day}:{shift}" for day, shift in scheduler_data['preferences']])
            if not preferred_str:
                preferred_str = 'nan'
            
            # Write to CSV
            writer.writerow([worker_name, unavailable_str, preferred_str, scheduler_data['day_off']])

def generate_new_schedule():
    """Helper function to generate and store a new schedule."""
    global current_schedule, current_assignments, WORKERS_DATA, ALL_WORKERS
    
    # Update CSV with availability data if any exists
    if WORKER_AVAILABILITY:
        update_workers_csv_from_availability()
        # Reload workers data from the updated CSV
        WORKERS_DATA = load_workers_from_csv('workers.csv')
        ALL_WORKERS = list(WORKERS_DATA.keys())
    
    current_schedule, current_assignments = schedule_shifts(WORKERS_DATA)

def process_excel_file(file_path):
    """Process Excel file and create CSV"""
    try:
        # Clear any cached data
        df = pd.read_excel(file_path)
        data = df.values
        
        # Ensure we have valid data
        if len(data) == 0:
            return False, "Excel file is empty"
        
        # Write to CSV with explicit encoding
        with open("workers.csv", mode="w", newline="", encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        
        # Force reload workers data after CSV update
        global WORKERS_DATA, ALL_WORKERS, current_schedule, current_assignments
        
        # Clear existing data
        WORKERS_DATA = {}
        ALL_WORKERS = []
        current_schedule = {}
        current_assignments = {}
        
        # Reload from the new CSV
        WORKERS_DATA = load_workers_from_csv('workers.csv')
        ALL_WORKERS = list(WORKERS_DATA.keys())
        
        # Generate new schedule immediately
        current_schedule, current_assignments = schedule_shifts(WORKERS_DATA)
        
        return True, f"CSV file created successfully! Loaded {len(ALL_WORKERS)} workers."
    except Exception as e:
        return False, f"Error processing file: {str(e)}"

@app.route('/')
def index():
    if not current_schedule:
        generate_new_schedule()
    
    return render_template('index.html', 
                           schedule=current_schedule, 
                           assignments=current_assignments, 
                           days_order=DAYS, 
                           shifts_order=SHIFTS,
                           all_workers=ALL_WORKERS)

@app.route('/availability')
def availability():
    return render_template('availability.html')

@app.route('/submit_availability', methods=['POST'])
def submit_availability():
    try:
        data = request.json
        
        worker_name = data.get('worker_name', '').strip()
        available_days = data.get('available_days', [])
        preferences = data.get('preferences', {})
        
        # Validation
        if not worker_name:
            return jsonify({'success': False, 'message': 'Worker name is required'})
        
        if not available_days:
            return jsonify({'success': False, 'message': 'At least one available day must be selected'})
        
        # Store the availability data with daily preferences
        WORKER_AVAILABILITY[worker_name] = {
            'available_days': available_days,
            'preferences': preferences
        }
        
        # Update the main workers data with converted format
        scheduler_data = convert_preferences_to_scheduler_format(worker_name, available_days, preferences)
        WORKERS_DATA[worker_name] = scheduler_data
        
        if worker_name not in ALL_WORKERS:
            ALL_WORKERS.append(worker_name)
        
        return jsonify({
            'success': True, 
            'message': f'Thank you {worker_name}! Your availability and daily preferences have been recorded.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing submission: {str(e)}'})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if file and file.filename.endswith('.xlsx'):
        # Generate a unique filename to avoid conflicts
        unique_filename = f"temp_{uuid.uuid4().hex}.xlsx"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        try:
            file.save(file_path)
            success, message = process_excel_file(file_path)
            
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            if success:
                # The schedule is already generated in process_excel_file
                return jsonify({
                    'success': True, 
                    'message': message,
                    'schedule': current_schedule,
                    'assignments': current_assignments
                })
            else:
                return jsonify({'success': False, 'message': message})
                
        except Exception as e:
            # Clean up file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'success': False, 'message': f'Error processing file: {str(e)}'})
    
    return jsonify({'success': False, 'message': 'Invalid file type. Please upload an Excel (.xlsx) file.'})

@app.route('/rerun')
def rerun():
    generate_new_schedule()
    ordered_schedule = {day: current_schedule[day] for day in DAYS if day in current_schedule}
    return jsonify({'schedule': ordered_schedule, 'assignments': current_assignments})

@app.route('/reset_week', methods=['POST'])
def reset_week():
    global WORKERS_DATA, ALL_WORKERS, current_schedule, current_assignments, WORKER_AVAILABILITY
    
    # Clear all worker data
    WORKERS_DATA = {}
    ALL_WORKERS = []
    current_schedule = {}
    current_assignments = {}
    WORKER_AVAILABILITY = {}
    
    # Clear the CSV file
    with open("workers.csv", mode="w", newline="", encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write empty file or just header if you prefer
        pass
    
    return jsonify({
        'success': True, 
        'message': 'All worker data has been cleared. Schedule has been reset.',
        'schedule': {},
        'assignments': {}
    })

@app.route('/update_shift', methods=['POST'])
def update_shift():
    global current_schedule, current_assignments
    data = request.json
    day = data.get('day')
    shift = data.get('shift')
    new_worker = data.get('new_worker')
    old_worker = current_schedule.get(day, {}).get(shift)

    # Update assignments count
    if old_worker and old_worker != "UNASSIGNED":
        current_assignments[old_worker] -= 1
    
    if new_worker and new_worker != "UNASSIGNED":
        current_assignments[new_worker] = current_assignments.get(new_worker, 0) + 1

    # Update the schedule
    current_schedule[day][shift] = new_worker
    
    return jsonify({'success': True, 'assignments': current_assignments})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
