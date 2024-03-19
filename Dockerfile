FROM python:3.10

RUN pip3 install poetry

WORKDIR /app

COPY pyproject.toml ./

RUN poetry install --no-root

COPY spamoverflow spamoverflow

# COPY spamhammer spamhammer

RUN dpkg --print-architecture | grep -q "amd64" && export SPAMHAMMER_ARCH="amd64" || export SPAMHAMMER_ARCH="arm64" && wget https://github.com/CSSE6400/SpamHammer/releases/download/v1.0.0/spamhammer-v1.0.0-linux-${SPAMHAMMER_ARCH} -O spamhammer && chmod +x spamhammer

CMD ["poetry", "run", "flask", "--app", "spamoverflow", "run", "--host", "0.0.0.0", "--port", "8080"]