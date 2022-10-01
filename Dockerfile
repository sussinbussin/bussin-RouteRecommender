FROM alpine:latest

RUN apk add py3-pip

WORKDIR /home

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 80

ENTRYPOINT ["/usr/bin/flask","run"]

CMD ["--host=0.0.0.0", "--port=80"]