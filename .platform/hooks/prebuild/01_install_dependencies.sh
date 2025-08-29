#!/bin/bash

# Enable the PostgreSQL 10 repository
sudo amazon-linux-extras enable postgresql10

# Install the PostgreSQL development libraries
sudo yum install -y postgresql-devel

# Install other necessary build tools
sudo yum install -y gcc