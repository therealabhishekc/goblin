export WHATSAPP_TOKEN="EAATVT98XGQsBPlvknyNpZBjLh4hGLyAZAxFqwz9RkZAX3ZBGcbnj0vnoXtb5BtT4BTl5Oj8YnZBspEe0G6NmeG4jqMGXt7CQsjkXrIOCc0anGEUxXjNwGHNrpyZAqvzAenyMRksunfXqztXmZA7daqqh9yaYiz3qH3LJZAmwitjDcMOLvxMvXREvRyAxVbB1BiBwUgZDZD" && export VERIFY_TOKEN="goblinhut" && export WHATSAPP_PHONE_NUMBER_ID="836277349562182"

./deploy-github.sh development us-east-1 "arn:aws:apprunner:us-east-1:461346075501:connection/abskgit/2435321c85da4c149f782706e3e989c9" "vpc-0a3bb06d8d6c02292" 

# Run migration as master user (since app_user doesn't have tables yet)
export PGPASSWORD='$cYKimo2nqLpH5#W>gnv*ySwSar('

psql -h whatsapp-postgres-development.cyd40iccy9uu.us-east-1.rds.amazonaws.com -p 5432 -U postgres -d whatsapp_business_development -f backend/migrations/complete_schema.sql

## Database TLS certificates

The backend now verifies the Amazon RDS certificate chain before opening a database connection. By default, the service downloads the latest bundle from the AWS Trust Store the first time it starts and caches it under `backend/app/core/certs/<region>-bundle.pem`.

- `DB_SSL_MODE` (default: `verify-full`) controls the libpq SSL mode. Avoid weakening this unless you are recovering from an outage.
- `DB_SSL_ROOT_CERT` can point to a pre-provisioned CA bundle if you manage the file outside the application container. If unset, the application writes the downloaded bundle to the default cache path above.
- `AWS_RDS_CERT_BUNDLE_URL` overrides the download location. Leave it empty to use the official regional bundle endpoint (for example, `https://truststore.pki.rds.amazonaws.com/us-east-1/us-east-1-bundle.pem`).

If the service cannot download or locate the bundle it falls back to the system trust store, which may trigger `certificate verify failed` errors. Ensure the runtime has outbound HTTPS access or pre-stage the bundle and set `DB_SSL_ROOT_CERT` accordingly.
