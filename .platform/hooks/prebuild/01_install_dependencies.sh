#!/bin/bash

# Enable the PostgreSQL 10 repository
sudo amazon-linux-extras enable postgresql10

# Install the PostgreSQL development libraries
sudo yum install -y postgresql-devel

# Install other necessary build tools
sudo yum install -y gcc

#!/bin/bash

# Activate the EB virtual environment
source /var/app/venv/*/bin/activate

# Install PhonePe SDK into that venv
pip install \
  --index-url https://phonepe.mycloudrepo.io/public/repositories/phonepe-pg-sdk-python \
  --extra-index-url https://pypi.org/simple \
  phonepe_sdk
