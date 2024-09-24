FROM mcr.microsoft.com/cbl-mariner/base/python:3

ENV ENVIRONMENT=DEV

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . /app

# Install required dependencies and utilities
RUN tdnf install -y \
    curl \
    unzip \
    libaio \
    unixODBC \
    unixODBC-devel \
    msodbcsql17 \
    cyrus-sasl-gssapi \
    openssl  # Install OpenSSL for SSL support

COPY drivers/simbaspark-2.8.2.1013-1.x86_64.rpm /tmp/

# Install the Databricks ODBC driver
#https://www.databricks.com/spark/odbc-drivers-archive#deb
RUN tdnf install --nogpgcheck -y /tmp/simbaspark-2.8.2.1013-1.x86_64.rpm && \
    rm -f /tmp/simbaspark-2.8.2.1013-1.x86_64.rpm

    # Set up ODBC driver configuration
RUN echo "[Simba Spark ODBC Driver]" > /etc/odbcinst.ini && \
    echo "Driver=/opt/simba/spark/lib/64/libsparkodbc_sb64.so" >> /etc/odbcinst.ini

EXPOSE 8000

ENTRYPOINT ["/bin/bash","./startup.sh"]

#docker run -e ENVIRONMENT=DEV -p 8000:8000 pdgdqsourceanalyzer:latest
