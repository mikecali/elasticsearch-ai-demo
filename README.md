**GenAI-Powered Search "using your own Data" Demo**

This repo contains artifacts & Python programs that can be use to ask a question regarding the data that was ingested and index into Elasticsearch Cloud and query them using a Retrieval Augmented Generation (RAG) demo app.

Pre-requisite
1. Setup your python virtual environment
2. Elastic Cloud Access - go to https://cloud.elastic.co/registration/ and register a new trial.

ElasticSearch Setup

1. Setup your Elastic Cloud with below details
   ```
      Name: your org 
      Cloud Provider: [any]
      Region: [any Australian region]
      Hardware profile: CPU Optimized OR CPU Optimized ARM
      Version: latest
   ```
2. Verify your deployment and make sure you have the following deployment

  ```
      3 Availability Zones
      2 Elasticsearch data nodes
      1 Elasticsearch tiebreaker node - 1 Enterprise Search node
      1 Integration Server node
      1 ML node
  ```

   
    
Quickstart 
1. Clone this repo
2. Enable python virtual environment

   ```source .venv/bin/activate```

3. Ensure dependencies are installed:

  ```pip3 install -r requirements.txt```

4. Make a copy of config.ini, rename it to something memorable, and fill out the required settings (note - you can choose Azure or Local LLM):

  ```
 [chat]
 OrganisationName = Orgname #something that will be displayed on your web app
 OrganisationCode = orgname-index #index name in ES

 [elastic]
 ElasticCloudId = Elastic cloud ID to send output to
 ElasticPassword = Elasticsearch password to use (optional if using api key)

 [gpt.openai]
 ApiKey = ChatGPT Key
 Model = gpt-4o
 Temperature = 0
```

5. Running our search app, Open a command/terminal window and navigate to the unzipped masterclass folder.

 ```
 pip install virtualenv
 source env/bin/activate
 pip install -r requirements.txt
 ```

6. Start the app. A new browser window should open! If it doesn’t, open a browser window and browse to http://localhost:8501

 ```
 streamlit run vic-sro.py
 ```

