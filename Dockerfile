FROM python:3.10

RUN pip3 install poetry

WORKDIR /app

COPY pyproject.toml ./

RUN poetry install --no-root

COPY spamoverflow spamoverflow

COPY spamhammer spamhammer
COPY inputs inputs
COPY outputs outputs

CMD ["poetry", "run", "flask", "--app", "spamoverflow", "run", "--host", "0.0.0.0", "--port", "8080"]