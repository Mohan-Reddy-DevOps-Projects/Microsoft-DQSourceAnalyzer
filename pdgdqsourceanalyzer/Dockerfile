FROM mcr.microsoft.com/cbl-mariner/base/python:3

ENV ENVIRONMENT=DEV

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
    ca-certificates

#RUN pip3 install -r requirements.txt
RUN pip3 install --extra-index-url=https://msdata.pkgs.visualstudio.com/4031b34e-6354-4257-94de-a85346a777ae/_packaging/PurviewDataGov/pypi/simple/ --trusted-host=msdata.pkgs.visualstudio.com -r requirements.txt

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
