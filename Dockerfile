# base image
FROM python:3.9-bullseye

# setup working directory
WORKDIR /code

# Install C, ffmpeg and graphics packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        libgl1-mesa-glx \
        libglib2.0-0 \
        poppler-utils\
    && rm -rf /var/lib/apt/lists/*

# Install all dependencies of opencv in bullseye
RUN apt-get update && apt-get install -y python3-opencv

# Copy pipfile and lockfile
COPY Pipfile Pipfile.lock /code/

# Install pipenv and install dependencies
RUN pip install pipenv && pipenv install --system

# Copy the app folder
COPY ./app ./app

# COPY .env .

RUN mkdir ./o2-files

# Expose port 
EXPOSE 8210

# Run fastapi using uvicorn
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8210", "--workers", "6", "--root-path", "/api/av"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8210", "--root-path", "/api/av"]
