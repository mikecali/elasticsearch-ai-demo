import openai
import requests
import json

gpt_model = ''
gpt_temperature = 0
localai_url_base = ''
localai_model = ''
localai_temperature = 0

def gpt_init(api_key, model, temperature):
    global gpt_model
    global gpt_temperature
    gpt_model = model
    gpt_temperature = float(temperature)
    openai.api_key = api_key
    print(f'gpt model:{gpt_model}, temperature:{gpt_temperature} ')

def localai_init(localai_url, Model_localai, Temperature_localai):
    global localai_model
    global localai_temperature
    global localai_url_base
    localai_model = Model_localai
    localai_temperature = float(Temperature_localai)
    localai_url_base = localai_url

def gpt_simple_send(messages, temperature):
    try:
        response = openai.ChatCompletion.create(
            model=gpt_model,
            messages=messages, 
            temperature=temperature
        )

        # Get the response and print it
        model_response = response.choices[0].message.content
        print(model_response)
        
        return response  # Return the entire response

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def localai_answers(messages, temperature):
    try:
        response = ask(json.dumps(messages)) 

        if response is None:
            raise ValueError("No response received from LocalAI")

        print(response)
        
        return response

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def ask(prompt):
    url = localai_url_base + '/v1/chat/completions'
    myobj = {
        "model": localai_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": localai_temperature
    }
    myheaders = { "Content-Type" : "application/json" }  

    try:
        print(f"Sending request to LocalAI: {url}")
        print(f"Request payload: {myobj}")
        x = requests.post(url, json=myobj, headers=myheaders)
        x.raise_for_status()  # Raise an error for bad status codes
        print(f"Response status code: {x.status_code}")
    except requests.RequestException as e:
        print(f"Error making request to LocalAI: {e}")
        return None
    
    try:
        json_data = x.json()
        print(f"Response JSON: {json_data}")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON response")
        return None

    # Logging the full response for debugging
    print("Full LocalAI response:", json_data)

    return json_data  # Return the entire JSON response
