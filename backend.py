from flask import Flask, render_template, request, jsonify
import openai
import json
import csv
from langchain.document_loaders import TextLoader, DirectoryLoader
from langchain.indexes import VectorstoreIndexCreator

API_KEY = ""
openai.api_key = API_KEY
app = Flask(__name__)

functions = [
    {
        "name": "row_orchestration",
        "description": "Determine the type of row UI and product to show",
        "parameters": {
            "type": "object",
            "properties": {
                "row_type": {
                    "type": "string",
                    "enum": ["table", "cards"],
                    "description": "Choose table if user wants to compare products or services and cards for exploration of options",
                },
                "prod_type":
                {
                    "type": "string",
                    "enum": ["plans", "devices", "information"],
                    "description": "The product inside the container",
                },
            },
            "required": ["row_type", "prod_type"],
        },
    },
    {
        "name": "get_devices",
        "description": "Retrieve a device or devices that the client is requesting.",
        "parameters": {
            "type": "object",
            "properties": {
                "focus":
                {
                    "type":"string",
                    "enum": ['Product', 'Display', 'Processor', 'RAM', 'Storage', 'Camera', 'Battery', 'Operating System', 'Connectivity', 'Overview'],
                    "description":"A label describing what attribute that is most important to the client in their request."
                },
                "items":
                {
                    "type": "array",
                    "items":{
                        "type":"string",
                        "description":"Name of device, e.g. Apple iPhone 15 Pro"
                    },
                    "description": "A list of a device or devices based on the focus of the client's request  and the available devices in the CSV provided",
                },
            },
            "required": ["focus","items"],
        },
    },
    {
        "name": "get_plans",
        "description": "Compose an array of plan names  that match what the client is looking for",
        "parameters": {
            "type": "object",
            "properties": {
                "items":
                {
                    "type": "array",
                    "items":{
                        "type":"string"
                    },
                    "description": "A list of plan names that match the constraints provided by the client",
                },
            },
            "required": ["items"],
        },
    },
    {
        "name": "focus",
        "description": "Get columns of csv headers that are alike to client's query",
        "parameters": {
            "type": "object",
            "properties": {
                "items":
                {
                    "type": "array",
                    "items":{
                        "type":"string",
                        "description":"Name of CSV header"
                    },
                    "description": "A list of CSV headers that are alike to client's query",
                },
            },
            "required": ["items"],
        },
    },
]

@app.route('/')
def index():
    return render_template('main.html')

@app.route('/process', methods=['POST'])
def process():
    print("before")
    data = request.form['data']
    print(data)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[{"role": "user", "content": f"{data}"}],
        functions=functions,
        function_call={"name":"row_orchestration"},  # auto is default, but we'll be explicit
        temperature=0
    )
    print(response)
    response_data = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])

    print(response_data["prod_type"])

    if response_data["prod_type"] == "devices":
        print("devices")
        headers = ""
        with open("basic.csv", 'r') as file:
            csv_reader = csv.reader(file)
            headers = next(csv_reader, None)
           
        with open("basic.csv", 'r') as file:
            print(headers)
            csv_reader = csv.DictReader(file)

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=[{"role": "user", "content": f"client is looking for:\n{data}\nheaders:\n{headers}"}],
                functions= functions,
                function_call={"name": "focus"}
            )
            response_data = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])

            row_text = "Product, "
            for title in response_data["items"]:
                    if title == "Product":
                        continue
                    row_text = row_text + title + ", "
            row_text = row_text + "\n"
            for row in csv_reader:
                # Process each row or column as needed
                row_as_string = ""
                row_as_string = row_as_string + row.get("Product") + ", "
                print(row_as_string)
                for title in response_data["items"]:
                    if title == "Product":
                        continue
                    row_as_string = row_as_string + row.get(title) + ", "
                row_text = row_text + row_as_string + '\n'
            
            print(row_text)

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=[{"role": "user", "content": f"CSV data for available devices and their attributes:\n{row_text}\n\nrequest:\nfrom the CSV data provided, {data}. Place all device or devices in a parsable array and do not provide any context."}],
                # functions= functions,
                # function_call={"name": "get_devices"}
            )
            print(response)
        return jsonify(result=response)
    elif response_data["prod_type"] == "plans":
        print("plans")
        with open("plans.csv", 'r') as file:
            csv_reader = csv.reader(file)
            row_text = ""
            for row in csv_reader:
                # Process each row or column as needed
                row_as_string = ', '.join(row)
                row_text = row_text + row_as_string + '\n\n'
            print(row_text)
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=[{"role": "user", "content": f"CSV data for available plans and their attributes:\n{row_text}\n\nrequest:\nfrom the CSV data provided, {data}. Place all plan or plans in a parsable array and do not provide any context."}],
                # functions= functions,
                # function_call={"name": "get_plans"}
            )
            print(response)
        return jsonify(result=response)
    else:
        return jsonify(result=response)

@app.route('/restrict', methods=['POST'])
def restrict():
    data = request.form['data']
    loader = DirectoryLoader(".", glob="*.csv")
    index = VectorstoreIndexCreator().from_loaders([loader])
    response = index.query(data)
    return jsonify(result=response)

if __name__ == '__main__':
    app.run(debug=True)