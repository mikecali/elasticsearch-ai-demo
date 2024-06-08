import openai
import tiktoken

model_max_tokens = {
    'gpt-3.5-turbo': 60000,
    'gpt-3.5-turbo-0301': 4000,
    'gpt-3.5-turbo-0613': 4000,
    'gpt-3.5-turbo-16k': 16000,
    'gpt-3.5-turbo-16k-0613': 16000,
    'gpt-4': 8000,
    'gpt-4-0314': 8000,
    'gpt-4-0613': 8000,
    'gpt-4-32k': 32000,
    'gpt-4-32k-0314': 32000,
    'gpt-4-32k-0613': 32000,
    'gpt-4o': 128000
}
gpt_max_tokens = 0
gpt_model = ''
gpt_temperature = 0

def gpt_init(api_key, model, temperature):
    global gpt_max_tokens
    global gpt_model
    global gpt_temperature
    gpt_max_tokens = model_max_tokens[model]
    gpt_model = model
    gpt_temperature = float(temperature)
    openai.api_key = api_key
    print(f'gpt model:{gpt_model}, temperature:{gpt_temperature} ')

def num_tokens_from_messages(messages, model):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print('Warning: model not found. Using cl100k_base encoding.')
        encoding = tiktoken.get_encoding('cl100k_base')
    if model in [
        'gpt-3.5-turbo',
        'gpt-3.5-turbo-0613',
        'gpt-3.5-turbo-16k-0613',
        'gpt-4-0314',
        'gpt-4-32k-0314',
        'gpt-4-0613',
        'gpt-4-32k-0613',
        'gpt-4-turbo',
        'gpt-4o'
    ]:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == 'gpt-3.5-turbo-0301':
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
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
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens

def gpt_get_available_token_count(messages) -> int:
    return gpt_max_tokens - num_tokens_from_messages(messages, gpt_model)

def gpt_simple_send(messages, temperature):
    num_tokens = num_tokens_from_messages(messages, gpt_model)
    if num_tokens > gpt_max_tokens:
        raise ValueError(f'Token limit exceeded: {num_tokens} > {gpt_max_tokens}')
    
    response = openai.chat.completions.create(
        model=gpt_model,
        messages=messages, 
        temperature=temperature
    )
   # Get the response and print it
    model_response = response.choices[0].message.content
    print(model_response)
#    # Add the response to the messages as an Assistant Role
#    messages.append({"role": "assistant", "content": model_response}) 
