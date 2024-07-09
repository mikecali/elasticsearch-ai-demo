# base image
# lets use the python image 3.9-slim
FROM python:3.9-slim

# exposing default port for streamlit
EXPOSE 8501

# making directory of app
WORKDIR /app

# copy over requirements
COPY requirements.txt ./requirements.txt

# install pip then packages
RUN pip3 install -r requirements.txt

# copying all files over
COPY . .

# cmd to launch app when container is run
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]

