FROM python

WORKDIR /code

COPY requirements.txt /code/

RUN pip install -r requirements.txt

COPY .key /code/

COPY bot /code/bot

CMD [ "python", "-m", "bot"]
