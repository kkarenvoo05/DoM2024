import importlib
import os
import re
from datetime import datetime
from typing import Tuple

from google.cloud import aiplatform
# Initialize the Vertex AI client
aiplatform.init(project='som-dom-brite', location='us-west1')

# Set the endpoint name
endpoint_name = "5474798248185036800"
endpoint = aiplatform.Endpoint(endpoint_name)

# Reading longer patient data from text file
def read_patient_data(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# Function to return the final response
def get_Prediction(prompt, patient_data):
    if patient_data != None:
        # Please provide only the specific piece of information asked for relating to the patient, without any additional general details. Do not provide any additional information.
        full_prompt = f"Patient Data: {patient_data}\nQuestion: {prompt}\nPlease provide a precise answer."
    else:
        full_prompt = prompt

    # print("Full Prompt: ", full_prompt)
    instances = [
        {
            "prompt": full_prompt,
            "max_tokens": 50,
            "temperature": 0.2,
            "top_p": 0.9,
            "top_k": 1,
        }
    ]
    # Get the prediction
    response = endpoint.predict(instances=instances)
    prediction = response.predictions[0]
    return prediction

def main():
    patient_data = None
    chosen_data_option = False

    while True:
        if not chosen_data_option:
            possible_patient_data = input("Do you have patient data? (yes/no): ").lower()
            if possible_patient_data == 'yes':
                file_path = input("Please enter the path to the patient data file: ")
                try:
                    patient_data = read_patient_data(file_path)
                    chosen_data_option = True
                except FileNotFoundError:
                    print("File not found. Please enter a valid file path.")
                    continue
            elif possible_patient_data == 'no':
                chosen_data_option = True
            else:
                print("Invalid input. Please enter 'yes' or 'no'.")
                continue

        action = input("Enter 'prompt' to enter a prompt, 'change data' to query different patient data, or 'quit' to exit: ").lower().strip()

        if not action:
            continue

        if action == 'quit':
            break
        elif action == 'change data':
            file_path = input("Please enter the path to the new patient data file (or press Enter to remove patient data): ")
            if file_path:
                try:
                    patient_data = read_patient_data(file_path)
                    print("Patient data updated.")
                except FileNotFoundError:
                    print("File not found. Please enter a valid file path.")
            else:
                patient_data = None
                print("Patient data removed.")
        elif action == 'prompt':
            prompt = input("Enter your prompt: ")
            result = get_Prediction(prompt, patient_data)
            print("Result:", result)
        else:
            print("Invalid input. Please enter 'prompt', 'change data', or quit.")

    print("Goodbye!")

if __name__ == "__main__":
    main()
