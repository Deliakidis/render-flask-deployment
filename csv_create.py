import csv
import pandas as pd
# # Data to write
data = []
# data = [
#     ["Name", "unavailable", "preferences"], 
#     ["Nantia", "Monday:Morning;Friday:Evening", "Saturday:Morning"],
#     ["Marinina", "Tuesday:Evening", "Wednesday:Evening"],
#     ["Dimitris","","Monday:Morning"]
# ]

# # Create and write to a CSV file
# with open("workers.csv", mode="w", newline="") as file:
#     writer = csv.writer(file)
#     writer.writerows(data)

# print("CSV file 'workers.csv' created successfully.")
df = pd.read_excel('raw.xlsx')
data = df.values  # This is a numpy array of all values
with open("workers.csv", mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerows(data)
# for i in range(len(data)):
#     for j in range(len(data[i])):

#         print(data[i][1])