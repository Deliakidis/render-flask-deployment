from app import convert_preferences_to_scheduler_format
from schedule import DAYS, SHIFTS

# Test the conversion function
test_data = {
    'worker_name': 'John',
    'available_days': ['Monday', 'Wednesday'],
    'preferences': {
        'Monday': {'Morning': 1, 'Afternoon': 2, 'Evening': 3},
        'Wednesday': {'Morning': 3, 'Afternoon': 1, 'Evening': 2}
    }
}

result = convert_preferences_to_scheduler_format(
    test_data['worker_name'], 
    test_data['available_days'], 
    test_data['preferences']
)

print('Conversion Result:')
print('Unavailable:', result['unavailable'])
print('Preferences:', result['preferences'])
print('Day off:', result['day_off'])

# Test if the format matches what the scheduler expects
print('\nTesting scheduler compatibility:')

# Simulate what the scheduler does
test_workers = {
    'John': result
}

# Test for Monday Morning (should be preferred)
day, shift = 'Monday', 'Morning'
if (day, shift) in test_workers['John']['unavailable']:
    print(f"{day} {shift}: Worker is unavailable")
elif (day, shift) in test_workers['John']['preferences']:
    print(f"{day} {shift}: Worker prefers this shift")
else:
    print(f"{day} {shift}: Worker is available but neutral")

# Test for Monday Evening (should be unavailable)
day, shift = 'Monday', 'Evening'
if (day, shift) in test_workers['John']['unavailable']:
    print(f"{day} {shift}: Worker is unavailable")
elif (day, shift) in test_workers['John']['preferences']:
    print(f"{day} {shift}: Worker prefers this shift")
else:
    print(f"{day} {shift}: Worker is available but neutral")

# Test for Tuesday Morning (should be unavailable - not in available days)
day, shift = 'Tuesday', 'Morning'
if (day, shift) in test_workers['John']['unavailable']:
    print(f"{day} {shift}: Worker is unavailable")
elif (day, shift) in test_workers['John']['preferences']:
    print(f"{day} {shift}: Worker prefers this shift")
else:
    print(f"{day} {shift}: Worker is available but neutral") 