# from base
FROM python:3.11-bullseye

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# setup working directory
WORKDIR /code

# Copy the app folder
COPY ./ .

RUN mkdir ./o2-files

# install deps
RUN pip install -r requirements.txt

# Expose port 
EXPOSE 8710

# Run fastapi using uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8710", "--reload"]
