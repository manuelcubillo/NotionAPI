FROM amazon/aws-lambda-python:3.8

RUN /var/lang/bin/python3.8 -m pip install --upgrade pip

COPY addToDB/requirements.txt .
RUN pip install -r requirements.txt

COPY addToDB/src/ .
COPY common/src/ .

CMD ["etl.handler"]