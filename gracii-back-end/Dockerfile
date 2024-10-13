FROM python:3.10-slim

WORKDIR /gracii_back_end

COPY . /gracii_back_end/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python3", "main.py"]