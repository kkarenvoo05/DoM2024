import sys
import sqlalchemy as db
import psycopg2
from psycopg2 import Error

from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import datetime
import subprocess
import json
 
x = datetime.datetime.now()
 
app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return "Hello!"

@app.route('/home', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Home Page"})

@app.route('/forms', methods=['POST'])
def forms():
    patID = request.form["Patient ID"]
    data = request.json
    return jsonify({"status": "success", "data": data})

@app.route('/prompts', methods=['GET'])
def get_prompts():
    prompts = ["Date of birth", #DG 1
               "Sex", #DG 2
               "Ethnicity", #DG 3
               "Race", #DG 4
               "Race Detail", #DG 5
               "Country of primary residence", #DG 6
               "Specify blood type", #SF 10
               "Specify Rh factor", #SF 11
               "Has the recipient signed an IRB / ethics committee (or similar body) approved consent form for submitting research data to the NMDP / CIBMTR?", #CN 12
               "Is the recipient participating in a clinical trial?", #CN 16
               "Multiple donors?", #SF 20
               "Specify the biological relationship of the donor to the recipient", #SF 25
               "Was this donor used for any prior HCTs?", #SF 28
               "Serum ferritin value", #LB 47
               "Serum albumin value", #LB 51
               ]
    return jsonify(prompts)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    patID = data['patID']
    selectedPrompts = data['selectedPrompts']

    print(patID)
    print(selectedPrompts)
    # result = subprocess.run(["python", "pipeline.py", str(patID)] + selectedPrompts, capture_output=True, text=True)
    result = subprocess.run([sys.executable, "pipeline.py", str(patID)] + selectedPrompts, capture_output=True, text=True)

    print(result)

    if result.returncode != 0:
        return jsonify({'error': 'Pipeline script failed', 'details': result.stderr}), 500

    try:
        output_strings = json.loads(result.stdout)
        if not isinstance(output_strings, list):
            raise ValueError("Expected a JSON array")
    except (json.JSONDecodeError, ValueError) as e:
        return jsonify({'error': 'Failed to parse pipeline output', 'details': str(e)}), 500

    return jsonify({
        'patID': patID,
        'selectedPrompts': selectedPrompts,
        'results': output_strings
    })
    

@app.route('/results', methods=['GET'])
def results():
    # response = jsonify(data)
    return "Hello"

if __name__ == '__main__':
    app.run(port=5001, debug=True)
