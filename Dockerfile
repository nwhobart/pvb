FROM python:alpine

RUN pip install redis requests semver prettytable

COPY main.py .

CMD ["python", "-u", "main.py"]