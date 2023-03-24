FROM python:alpine

RUN pip install redis requests semver prettytable

ENV REDIS_HOSTNAME="localhost"
ENV REDIS_PORT="6379"

COPY main.py .

CMD ["python", "-u", "main.py"]
