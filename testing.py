import csv

with open("basic.csv", 'r') as file:
            csv_reader = csv.reader(file)
            headers = next(csv_reader, None)
           
            print(headers)