FROM python:3.9.10

USER root

# set work directory
WORKDIR /opt/app-root/src

# install psycopg2 dependencies
RUN apt update
RUN apt install ffmpeg libsm6 libxext6  -y

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
COPY ./ .
RUN pip install -r requirements.txt
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /opt/app-root/src/entrypoint.sh
RUN chmod +x /opt/app-root/src/entrypoint.sh
COPY ./env.test ./.env
#CMD [ "python", "./manage.py" ]
ENTRYPOINT ["/opt/app-root/src/entrypoint.sh"]
