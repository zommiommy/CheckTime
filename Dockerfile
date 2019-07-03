# Use a container with influxdb on and the basic shell utils
from ubuntu:18.04

RUN \
  apt-get update && \
  apt-get install -y gcc time vim wget curl bash software-properties-common apt-utils && \
  apt-get upgrade -y 

# Install infuxdb
RUN curl -sL https://repos.influxdata.com/influxdb.key | apt-key add -
RUN echo "deb https://repos.influxdata.com/ubuntu trusty stable" | tee /etc/apt/sources.list.d/influxdb.list
RUN apt-get update && apt-get -y install influxdb
# Enable and start the DB
RUN systemctl enable influxdb
RUN systemctl start influxdb

# Crate the folder where we will work
RUN mkdir -p /checktime

# Copy all the folder to the container
# project is a symbolic link to ../ to workaround the fact that 
# docker only allows to add folder under the build directory
ADD ./ /checktime

# Load the test data
RUN /checktime/check_time_env/bin/python /checktime/test_env/load_data_to_db.py