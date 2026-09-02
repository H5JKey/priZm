FROM python:3.13-bookworm

WORKDIR /backend

RUN pip install poetry

COPY backend .

RUN poetry config virtualenvs.create false

RUN poetry install

RUN chmod +x prestart.sh

ENTRYPOINT ["./prestart.sh"]

CMD ["uvicorn", "main:app","--host", "0.0.0.0", "--port", "8000", "--reload"]