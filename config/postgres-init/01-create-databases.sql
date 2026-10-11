-- Lab3: separate sandbox and production databases for environment isolation.
-- Runs automatically on a fresh Postgres volume (docker-entrypoint-initdb.d).
CREATE DATABASE cyberimplant_sandbox;
CREATE DATABASE cyberimplant_prod;
