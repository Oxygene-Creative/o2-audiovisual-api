# base image
# FROM python:3.10-alpine
FROM python:3.10-bullseye

# setup working directory
WORKDIR /code

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        libgl1-mesa-glx \
        libglib2.0-0 \
        poppler-utils\
    && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y python3-opencv

# Install C, ffmpeg and graphics packages if using alpine distro
# RUN apk add --no-cache \
#     gcc \
#     musl-dev \
#     libffi-dev \
#     ffmpeg \
#     mesa-gl \
#     glib \
#     poppler-utils \
#     opencv \
#     py3-opencv \
#     py3-numpy \
#     py3-pip \
#     && pip install --upgrade pip

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
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8210", "--root-path", "/api/av"]
