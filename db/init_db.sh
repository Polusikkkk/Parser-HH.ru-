#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE USER practica WITH PASSWORD '12345';
  CREATE DATABASE practica_db;
  GRANT ALL PRIVILEGES ON DATABASE practica_db TO practica;
  ALTER DATABASE practica_db OWNER TO practica;
EOSQL