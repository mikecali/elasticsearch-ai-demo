import openai
import tiktoken
import requests
import json

model_max_tokens = {
    'gpt-4o': 128000
}
gpt_max_tokens = 0
gpt_model = ''
gpt_temperature = 0
localai_url_base = ''

def gpt_init(api_key, model, temperature):
    global gpt_max_tokens
    global gpt_model
    global gpt_temperature
    gpt_max_tokens = model_max_tokens[model]
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

def num_tokens_from_messages(messages, model):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print('Warning: model not found. Using cl100k_base encoding.')
        encoding = tiktoken.get_encoding('cl100k_base')
    if model in [
        'gpt-3.5-turbo',
        'gpt-4o'
    ]:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == 'gpt-3.5-turbo-0301':
        tokens_per_message = 4  # every message follows {role/name}\n{content}\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif 'gpt-3.5-turbo' in model:
        print('Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.')
        return num_tokens_from_messages(messages, model='gpt-3.5-turbo-0613')
    elif 'gpt-4' in model:
        print('Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.')
        return num_tokens_from_messages(messages, model='gpt-4-0613')
    else:
        raise NotImplementedError(
            f'num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.'
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == 'name':
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with assistant
    return num_tokens

def gpt_get_available_token_count(messages) -> int:
    return gpt_max_tokens - num_tokens_from_messages(messages, gpt_model)

def gpt_simple_send(messages, temperature):
    try:
        response = openai.chat.completions.create(
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