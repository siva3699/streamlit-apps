FROM python:3.10
COPY . /app
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 80
RUN mkdir ~/.streamlit
#RUN cp .streamlit/config.toml ~/.streamlit/config.toml
#RUN cp .streamlit/credentials.toml ~/.streamlit/credentials.toml
WORKDIR /app
ENTRYPOINT ["streamlit", "run"]
CMD ["app.py"]
