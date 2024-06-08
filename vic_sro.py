import configparser
import elasticsearch
import json
import streamlit as st

from gpt_openai_client import gpt_init, gpt_get_available_token_count, gpt_simple_send

# read config file
CONFIG = configparser.ConfigParser()
CONFIG.read('vic_sro.ini')

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
    api_key = CONFIG['gpt.openai']['ApiKey'],
    model = CONFIG['gpt.openai']['Model'],
    temperature = CONFIG['gpt.openai']['Temperature']
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

# Example usage with dummy data
hits = [
    {
        "_source": {
            "title": "Home Loan",
            "url" : "https://www.metrobank.com.ph",
            "body_content" : "Hello Metrobank"
        },
        "_score": 1
    }
]

# Print the results
print(md_elastic_results(hits))


# execute a simple lexical search against Elasticsearch
def lexical_search(client: elasticsearch.Elasticsearch, query_string:str):
    if not client.indices.exists(index=ELASTIC_INDEX):
        raise ValueError(f'Unable to search: Index "{ELASTIC_INDEX}" does not exist.')

    response = client.search(
        index=ELASTIC_INDEX,
        query={
            'multi_match' : {
                'query' : query_string,
                'type' : 'best_fields',
                'fields' : ['body_content', 'title^2']
            }
        },
        size=5,
        source_includes=['body_content', 'title', 'url']
    )
    return response['hits']['hits']

# execute an ELSER search against Elasticsearch
def elser_search(client: elasticsearch.Elasticsearch, query_string:str):
    if not client.indices.exists(index=ELASTIC_INDEX):
        raise ValueError(f'Unable to search: Index "{ELASTIC_INDEX}" does not exist.')
    properties = esclient.indices.get_mapping(index=ELASTIC_INDEX)[ELASTIC_INDEX]['mappings']['properties']
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
            "bool" : {
                "should" : [
                    {
                        "text_expansion": {
                            "ml.inference.body_content_expanded.predicted_value" : {
                                "model_id" : ".elser_model_2_linux-x86_64",
                                "model_text" : query_string
                            }
                        }
                    },
                    {
                        "text_expansion": {
                            "ml.inference.title_expanded.predicted_value" : {
                                "model_id" : ".elser_model_2_linux-x86_64",
                                "model_text" : query_string
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
def hybrid_search(client: elasticsearch.Elasticsearch, query_string:str):
    search_applications = esclient.search_application.list()
    if search_applications['count'] == 0 or ELASTIC_SEARCH_APPLICATION not in [r['name'] for r in search_applications['results']]:
        raise ValueError(f'Unable to search: Search Application "{ELASTIC_SEARCH_APPLICATION}" does not exist.')

    response = client.search_application.search(
        name=ELASTIC_SEARCH_APPLICATION,
        params={
            'query_string' : query_string,
            'size' : 5
        }
    )
    return response['hits']['hits']

# Send the initial prompt to the LLM elaborating its purpose in this conversation
def answer(hits, query_string):
    system = f""" Metrobank Debug"""
    context = []
    for hit in hits:
        context.append(hit['_source'])
        messages = [
            { 'role' : 'system', 'content' : f'system\n{json.dumps(context)}' },
            { 'role' : 'user', 'content' : query_string }
        ]
        if(gpt_get_available_token_count(messages) < 300):
            context = context[:-1]
            break
    print(len(context))
    messages = [
        { 'role' : 'system', 'content' : f'system\n{json.dumps(context)}' },
        { 'role' : 'user', 'content' : query_string }
    ]
    return gpt_simple_send(messages,1)['choices'][0]['message']['content'].replace('$', '\\$')

 #   client = OpenAI(api_key=openai_api_key)
 #   st.session_state.messages.append({"role": "user", "content": prompt})
 #   st.chat_message("user").write(prompt)
 #   response = client.chat.completions.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
 #   msg = response.choices[0].message.content



esclient = elasticsearch.Elasticsearch(
    cloud_id=ELASTIC_CLOUD_ID,
    basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD)
)

st.title(CHAT_NAME)
query = st.text_input('You want to know: ')

lexicalTab, elserTab, hybridTab, chatTab, finishedTab = st.tabs(['Lexical Search', 'ELSER Search', 'Hybrid Search', 'ChatGPT Questions', 'I\'m Finished!'])

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
#            hits = hybrid_search(esclient, query)
            st.write(answer(hits, query))
        except ValueError as ex:
            st.error(ex)
 #   st.session_state.messages.append({"role": "assistant", "content": msg})
 #   st.chat_message("assistant").write(msg)


with finishedTab:
    finished_submit_button = st.button('Finished!', 'btn_finished')
    if finished_submit_button:
        # Once the ask button has been clicked...
        st.balloons()
