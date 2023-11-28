FROM ubuntu:latest
RUN apt-get update \
    && apt-get install -y python3.10 python3-pip \
    && apt-get install -y curl libc6-dev
RUN curl https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc 
RUN curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list | tee /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update
RUN dpkg-reconfigure dash
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && ACCEPT_EULA=Y apt-get install -y mssql-tools \
    && echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc \
    && apt-get install -y unixodbc-dev
COPY . /app
WORKDIR /app
RUN curl https://bootstrap.pypa.io/get-pip.py
RUN export PATH="$HOME/.local/bin:$PATH"
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 80
RUN mkdir ~/.streamlit
RUN cp .streamlit/config.toml ~/.streamlit/config.toml
#RUN cp .streamlit/credentials.toml ~/.streamlit/credentials.toml
WORKDIR /app
ENTRYPOINT ["streamlit", "run"]
CMD ["app.py"]
