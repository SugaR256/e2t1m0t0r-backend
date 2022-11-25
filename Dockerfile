# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-bullseye

EXPOSE 5000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV PRODUCTION=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app
COPY sources.list /etc/apt
ENV LD_LIBRARY_PATH /app/libs

RUN apt update
RUN apt install --only-upgrade gcc -y

RUN mkdir temp

ENTRYPOINT [ "python" ]
CMD [ "main.py" ]
