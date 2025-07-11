import csv
import random
import pandas as pd


DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
SHIFTS = ['Morning', 'Afternoon', 'Evening']

def load_workers_from_csv(filename):
    workers = {}
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) < 1:
                continue
                
            name = row[0].strip()
            if not name:  # Skip empty rows
                continue
                
            # Handle unavailable times (column 1)
            unavailable = []
            if len(row) > 1 and row[1].strip() and row[1].strip().lower() != 'nan':
                unavailable = [tuple(x.strip().split(':')) for x in row[1].split(';') if x.strip()]
            
            # Handle preferences (column 2)
            preferences = []
            if len(row) > 2 and row[2].strip() and row[2].strip().lower() != 'nan':
                preferences = [tuple(x.strip().split(':')) for x in row[2].split(';') if x.strip()]
            
            # Handle day off (column 3)
            day_off = ''
            if len(row) > 3 and row[3].strip() and row[3].strip().lower() != 'nan':
                day_off = row[3].strip()
            
            workers[name] = {
                'unavailable': unavailable,
                'preferences': preferences,
                'day_off': day_off
            }
    return workers

def schedule_shifts(workers):
    """
    Fair scheduling algorithm that:
    - Prevents double shifts (no worker works multiple shifts on same day)
    - Distributes shifts fairly among available workers
    - Respects worker preferences and availability
    - Minimizes consecutive work days
    """
    if not workers:
        return {}, {}
    
    # Initialize tracking
    shift_assignments = {w: 0 for w in workers}  # Total shifts per worker
    daily_assignments = {w: set() for w in workers}  # Days each worker is assigned
    consecutive_days = {w: 0 for w in workers}  # Track consecutive work days
    last_work_day = {w: None for w in workers}  # Last day each worker worked
    
    schedule = {day: {} for day in DAYS}
    
    # First pass: assign preferred shifts
    for day in DAYS:
        for shift in SHIFTS:
            if schedule[day].get(shift):  # Skip if already assigned
                continue
                
            # Find workers who prefer this shift and are available
            preferred_workers = []
            for worker in workers:
                if (day, shift) in workers[worker]['preferences']:
                    if (day, shift) not in workers[worker]['unavailable']:
                        if workers[worker]['day_off'].lower() != day.lower():
                            if day not in daily_assignments[worker]:  # No double shifts
                                preferred_workers.append(worker)
            
            if preferred_workers:
                # Choose worker with fewest total shifts and no consecutive days
                best_worker = min(preferred_workers, 
                                key=lambda w: (shift_assignments[w], 
                                             consecutive_days[w],
                                             -len(workers[w]['preferences'])))  # Prefer workers with more preferences
                schedule[day][shift] = best_worker
                shift_assignments[best_worker] += 1
                daily_assignments[best_worker].add(day)
                
                # Update consecutive days tracking
                if last_work_day[best_worker] is not None:
                    day_diff = DAYS.index(day) - DAYS.index(last_work_day[best_worker])
                    if day_diff == 1:  # Consecutive day
                        consecutive_days[best_worker] += 1
                    else:
                        consecutive_days[best_worker] = 0
                else:
                    consecutive_days[best_worker] = 0
                last_work_day[best_worker] = day
    
    # Second pass: fill remaining shifts fairly
    for day in DAYS:
        for shift in SHIFTS:
            if schedule[day].get(shift):  # Skip if already assigned
                continue
                
            # Find all available workers for this shift
            available_workers = []
            for worker in workers:
                if (day, shift) not in workers[worker]['unavailable']:
                    if workers[worker]['day_off'].lower() != day.lower():
                        if day not in daily_assignments[worker]:  # No double shifts
                            available_workers.append(worker)
            
            if not available_workers:
                schedule[day][shift] = "UNASSIGNED"
                continue
            
            # Choose worker with best fairness score
            def fairness_score(worker):
                total_shifts = shift_assignments[worker]
                consecutive_penalty = consecutive_days[worker] * 2  # Penalize consecutive days
                preference_bonus = len([(d, s) for d, s in workers[worker]['preferences'] 
                                      if d == day and s == shift]) * 3  # Bonus for preference
                return (total_shifts + consecutive_penalty - preference_bonus)
            
            best_worker = min(available_workers, key=fairness_score)
            schedule[day][shift] = best_worker
            shift_assignments[best_worker] += 1
            daily_assignments[best_worker].add(day)
            
            # Update consecutive days tracking
            if last_work_day[best_worker] is not None:
                day_diff = DAYS.index(day) - DAYS.index(last_work_day[best_worker])
                if day_diff == 1:  # Consecutive day
                    consecutive_days[best_worker] += 1
                else:
                    consecutive_days[best_worker] = 0
            else:
                consecutive_days[best_worker] = 0
            last_work_day[best_worker] = day
    
    return schedule, shift_assignments

    def readExcel(file) :

        dataframe = pd.read_excel(file)
        print(dataframe.columns)
