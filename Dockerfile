FROM python

WORKDIR /code

COPY requirements.txt /code/

RUN pip install -r requirements.txt

COPY . /code

CMD [ "python", "-m", "bot"]
