***GenAI-Powered Search "using your own Data" Demo***

This repo contains artifacts (in snippets.tex) & Python programs that can be use to ask a question regarding the data that was ingested and index into Elasticsearch Cloud and query them using a Retrieval Augmented Generation (RAG) demo app.

Pre-requisite
1. Setup your python virtual environment, once setup is complete
    ```
     virtualenv venv
     source venv/bin/activate
    ```
3. Elastic Cloud Access - go to https://cloud.elastic.co/registration/ and register a new trial.

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

3. Uploading Contents
   Get a dataset from your website of choice. We will setup a crawler to that website and index the data to ES.
   There will be some extra steps that you need to follow to properly massage the data that you need:
    
   - From your ESS menu go to Search tab and select Web Crawler, click start.
   - Make sure that you remember the name of your index.
   - Then set the domain of the website that you need to crawl, validate domain and add domain - www.nba.com as example
   - Test your domain by clicking the "Crawl", then select "crawl all domain on this index" to begin crawling the website.
   - The crawler should start crawling content pretty much immediately, so you should be able to have a look at the documents. From the “Search” menu under “Content” click “Indices”. Then click on the “index you created" index   - To see the documents that have been indexed click on “Documents”, now you can see some of the web pages that have been indexed. You can do a basic search through them if you want! Pick a document, and open it up by clicking on the expand button.
   - Analyse the document and look for things that you can update/change - this is where you need to massage the data to make sure you crawl the right information that needs to be index to Elasticsearch

4. Voila, you got your data setup and is ready to use.
   NOTE: There is always a need to massage the data and you need to do this by going to this steps:
   
    
**Quickstart**
 
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
  virtualenv venv
  source env/bin/activate
  pip install -r requirements.txt
 ```

6. Start the app. A new browser window should open! If it doesn’t, open a browser window and browse to http://localhost:8501

 ```
   streamlit run main.py
 ```

Example Results:


![Image 11-6-2024 at 10 00 AM](https://github.com/mikecali/elasticsearch-ai-demo/assets/17167732/ac84bcd1-dd7d-4051-b97e-c1b8ebfad13c)

