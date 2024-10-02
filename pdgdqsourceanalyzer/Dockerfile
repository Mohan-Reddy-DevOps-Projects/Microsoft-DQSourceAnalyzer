FROM mcr.microsoft.com/cbl-mariner/base/python:3

ENV ENVIRONMENT=DEV

#ARG PIP_EXTRA_INDEX_URL

ARG PIP_INDEX_URL

ENV PIP_INDEX_URL=$PIP_INDEX_URL

WORKDIR /app

COPY requirements.txt requirements.txt

COPY . /app

# Install required dependencies and utilities
RUN tdnf install -y \
    curl \
    unzip \
    libaio \
    unixODBC \
    unixODBC-devel \
    cyrus-sasl-gssapi \
    openssl  \
    openssl-devel \
    ca-certificates

#RUN pip3 install -r requirements.txt --extra-index-url https://$PIP_USERNAME:$PIP_PASSWORD@msdata.pkgs.visualstudio.com/_packaging/PurviewDataGov/pypi/simple

RUN pip3 install -r requirements.txt --index-url $PIP_INDEX_URL

RUN ACCEPT_EULA=Y yum install -y msodbcsql17 && \
    yum clean all

COPY drivers/simbaspark-2.8.2.1013-1.x86_64.rpm /tmp/

# Install the Databricks ODBC driver
#https://www.databricks.com/spark/odbc-drivers-archive#deb
RUN tdnf install --nogpgcheck -y /tmp/simbaspark-2.8.2.1013-1.x86_64.rpm && \
    rm -f /tmp/simbaspark-2.8.2.1013-1.x86_64.rpm

# Configure ODBC Driver
RUN echo "[Simba Spark ODBC Driver]" > /etc/odbcinst.ini && \
    echo "Description=Simba Spark ODBC Driver" >> /etc/odbcinst.ini && \
    echo "Driver=/opt/simba/spark/lib/64/libsparkodbc_sb64.so" >> /etc/odbcinst.ini && \
    echo "UsageCount=1" >> /etc/odbcinst.ini


EXPOSE 8000

ENTRYPOINT ["/bin/bash","./startup.sh"]

#docker run -e ENVIRONMENT=DEV -p 8000:8000 pdgdqsourceanalyzer:latest
