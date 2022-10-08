# FROM alpine:latest

# RUN apk add py3-pip

# WORKDIR /home

# COPY requirements.txt requirements.txt
# RUN pip3 install -r requirements.txt

# COPY . .

# EXPOSE 80

# CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=80"]

#!/bin/bash

FROM alpine:latest

RUN apk add py3-pip

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]