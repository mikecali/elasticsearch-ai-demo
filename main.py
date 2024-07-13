import configparser
import elasticsearch
import json
import streamlit as st

from gpt_openai_client import gpt_init, gpt_simple_send, localai_init, localai_answers

# read config file
CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')

# get some basic properties of the conversation
ORGANISATION_NAME = CONFIG['chat']['OrganisationName']
CHAT_NAME = CONFIG['chat']['ChatName']
ORGANISATION_CODE = CONFIG['chat']['OrganisationCode']

# get some Elastic Search settings
ELASTIC_CLOUD_ID = CONFIG['elastic']['ElasticCloudId']
ELASTIC_USERNAME = 'elastic'
ELASTIC_PASSWORD = CONFIG['elastic']['ElasticPassword']
ELASTIC_INDEX = f'search-{ORGANISATION_CODE}'
ELASTIC_SEARCH_APPLICATION = f'{ORGANISATION_CODE}-simple'

# init the OpenAI ChatGPT client
gpt_init(
    api_key=CONFIG['gpt.openai']['ApiKey'],
    model=CONFIG['gpt.openai']['Model'],
    temperature=CONFIG['gpt.openai']['Temperature']
)

# init the LocalAI client
localai_init(
    localai_url=CONFIG['localai.openai']['localaiURL'],
    Model_localai=CONFIG['localai.openai']['Model_localai'],
    Temperature_localai=CONFIG['localai.openai']['Temperature_localai']
)

# Converts a crawled Elasticsearch JSON document into markdown text so it's a bit easier to read
def md_elastic_result(hit, id):
    title = f'### {id} - [{hit["_source"]["title"]}]({hit["_source"]["url"]})'
    score = f'**Score:** `{hit["_score"]}`'
    body_content = hit["_source"]["body_content"].replace('$', '\\$')

    # Adding newlines for better readability
    formatted_body_content = '\n\n'.join(body_content.split('\n\n'))

    return '\n\n'.join([title, score, formatted_body_content])

# Converts a list of crawled Elasticsearch JSON documents into markdown text so they're a bit easier to read
def md_elastic_results(hits):
    id = 1
    results = []
    for hit in hits:
        results.append(md_elastic_result(hit, id))
        id = id + 1
    return '\n\n'.join(results)

# execute a simple lexical search against Elasticsearch
def lexical_search(client: elasticsearch.Elasticsearch, query_string: str):
    if not client.indices.exists(index=ELASTIC_INDEX):
        raise ValueError(f'Unable to search: Index "{ELASTIC_INDEX}" does not exist.')

    response = client.search(
        index=ELASTIC_INDEX,
        query={
            'multi_match': {
                'query': query_string,
                'type': 'best_fields',
                'fields': ['body_content', 'title^2']
            }
        },
        size=5,
        source_includes=['body_content', 'title', 'url']
    )
    return response['hits']['hits']

# execute an ELSER search against Elasticsearch
def elser_search(client: elasticsearch.Elasticsearch, query_string: str):
    if not client.indices.exists(index=ELASTIC_INDEX):
        raise ValueError(f'Unable to search: Index "{ELASTIC_INDEX}" does not exist.')
    properties = client.indices.get_mapping(index=ELASTIC_INDEX)[ELASTIC_INDEX]['mappings']['properties']
    try:
        if properties['ml']['properties']['inference']['properties']['body_content_expanded']['properties']['predicted_value']['type'] not in ['rank_features', 'sparse_vector']:
            raise ValueError(f'Unable to search: Field "ml.inference.body_content_expanded.predicted_value" in index "{ELASTIC_INDEX}" needs to be of type "sparse_vector".')
    except KeyError:
        raise ValueError(f'Unable to search: Field "ml.inference.body_content_expanded.predicted_value" does not exist in index "{ELASTIC_INDEX}".')
    try:
        if properties['ml']['properties']['inference']['properties']['title_expanded']['properties']['predicted_value']['type'] not in ['rank_features', 'sparse_vector']:
            raise ValueError(f'Unable to search: Field "ml.inference.title_expanded.predicted_value" in index "{ELASTIC_INDEX}" needs to be of type "sparse_vector".')
    except KeyError:
        raise ValueError(f'Unable to search: Field "ml.inference.title_expanded.predicted_value" does not exist in index "{ELASTIC_INDEX}".')

    response = client.search(
        index=ELASTIC_INDEX,
        query={
            "bool": {
                "should": [
                    {
                        "text_expansion": {
                            "ml.inference.body_content_expanded.predicted_value": {
                                "model_id": ".elser_model_2_linux-x86_64",
                                "model_text": query_string
                            }
                        }
                    },
                    {
                        "text_expansion": {
                            "ml.inference.title_expanded.predicted_value": {
                                "model_id": ".elser_model_2_linux-x86_64",
                                "model_text": query_string
                            }
                        }
                    }
                ]
            }
        },
        size=5,
        source_includes=['body_content', 'title', 'url']
    )
    return response['hits']['hits']

# execute a hybrid search using an Elasticsearch Search Application
def hybrid_search(client: elasticsearch.Elasticsearch, query_string: str):
    search_applications = client.search_application.list()
    if search_applications['count'] == 0 or ELASTIC_SEARCH_APPLICATION not in [r['name'] for r in search_applications['results']]:
        raise ValueError(f'Unable to search: Search Application "{ELASTIC_SEARCH_APPLICATION}" does not exist.')

    response = client.search_application.search(
        name=ELASTIC_SEARCH_APPLICATION,
        params={
            'query_string': query_string,
            'size': 5
        }
    )
    return response['hits']['hits']

# Ask ChatGPT
def answer(hits, query_string):
    system = f"""RAG Debug"""
    context = []
    for hit in hits:
        context.append(hit['_source'])
        messages = [
            {'role': 'system', 'content': f'system\n{json.dumps(context)}'},
            {'role': 'user', 'content': query_string}
        ]

    # Construct the final messages
    messages = [
        {'role': 'system', 'content': f'system\n{json.dumps(context)}'},
        {'role': 'user', 'content': query_string}
    ]

    # Get the response from GPT
    response = gpt_simple_send(messages, 1)
    model_response = response.choices[0].message.content
    print(model_response)

    # Extract the content of the first choice
    response.choices[0].message.content
    message_content = model_response
    return message_content.replace('$', '\\$')

# Ask LocalAI
def localaianswer(hits, query_string, selected_model):
    system = f"""localAI Debug"""
    context = []
    for hit in hits:
        context.append(hit['_source'])
        messages = [
            {'role': 'system', 'content': f'system\n{json.dumps(context)}'},
            {'role': 'user', 'content': query_string}
        ]

    # Construct the final messages
    messages = [
        {'role': 'system', 'content': f'system\n{json.dumps(context)}'},
        {'role': 'user', 'content': query_string}
    ]

    # Get the response from LocalAI
    response = localai_answers(messages, selected_model)

    if not response:
        raise ValueError("No response received from LocalAI")

    # Debugging: Print full response
    print("Full response:", response)

    # Ensure the response is in the expected format
    if "choices" not in response or not isinstance(response["choices"], list) or not response["choices"]:
        print("Error: Invalid response structure from LocalAI")
        raise ValueError("Invalid response structure from LocalAI")

    local_model_response = response["choices"][0].get("message", {}).get("content")
    if not local_model_response:
        print("Error: Content not found in LocalAI response")
        raise ValueError("Content not found in LocalAI response")

    print("LocalAI response content:", local_model_response)

    # Extract the content of the first choice
    message_content = local_model_response
    return message_content.replace('$', '\\$')

esclient = elasticsearch.Elasticsearch(
    cloud_id=ELASTIC_CLOUD_ID,
    basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD)
)

st.title(CHAT_NAME)
query = st.text_input('You want to know: ')

lexicalTab, elserTab, hybridTab, chatTab, localaiTab = st.tabs(['Lexical Search', 'ELSER Search', 'Hybrid Search', 'ChatGPT Questions', 'LocalAI'])

with lexicalTab:
    lexical_submit_button = st.button('Search', 'btn_lexical_search')
    if lexical_submit_button:
        # Once the search button has been clicked...
        try:
            st.write(md_elastic_results(lexical_search(esclient, query)))
        except ValueError as ex:
            st.error(ex)

with elserTab:
    elser_submit_button = st.button('Search', 'btn_elser_search')
    if elser_submit_button:
        # Once the search button has been clicked...
        try:
            st.write(md_elastic_results(elser_search(esclient, query)))
        except ValueError as ex:
            st.error(ex)

with hybridTab:
    hybrid_submit_button = st.button('Search', 'btn_hybrid_search')
    if hybrid_submit_button:
        # Once the search button has been clicked...
        try:
            st.write(md_elastic_results(hybrid_search(esclient, query)))
        except ValueError as ex:
            st.error(ex)

with chatTab:
    chat_submit_button = st.button('Ask', 'btn_chat_ask')
    if chat_submit_button:
        # Once the ask button has been clicked...
        try:
            hits = hybrid_search(esclient, query)
            st.write(answer(hits, query))
        except ValueError as ex:
            st.error(ex)

with localaiTab:
    model_options = ["gpt-4", "gpt-3.5-turbo", "ggml-gpt4all-j.bin"]  # Add your model options here
    selected_model = st.selectbox('Select a model:', model_options)

    chat_submit_button = st.button('Ask', 'btn_localai_ask')
    if chat_submit_button:
        # Once the ask button has been clicked...
        try:
            hits = hybrid_search(esclient, query)
            response = localaianswer(hits, query, selected_model)
            print("Displaying response on Streamlit page:", response)  # Ensure this is printed
            st.write(response)  # Display the response on the webpage
        except ValueError as ex:
            st.error(ex)
