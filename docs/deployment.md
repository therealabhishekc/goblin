export WHATSAPP_TOKEN="EAATVT98XGQsBPlvknyNpZBjLh4hGLyAZAxFqwz9RkZAX3ZBGcbnj0vnoXtb5BtT4BTl5Oj8YnZBspEe0G6NmeG4jqMGXt7CQsjkXrIOCc0anGEUxXjNwGHNrpyZAqvzAenyMRksunfXqztXmZA7daqqh9yaYiz3qH3LJZAmwitjDcMOLvxMvXREvRyAxVbB1BiBwUgZDZD" && export VERIFY_TOKEN="goblinhut" && export WHATSAPP_PHONE_NUMBER_ID="836277349562182"

./deploy-github.sh development us-east-1 "arn:aws:apprunner:us-east-1:461346075501:connection/abskgit/2435321c85da4c149f782706e3e989c9" "vpc-0a3bb06d8d6c02292" 

# Run migration as master user (since app_user doesn't have tables yet)
export PGPASSWORD='$cYKimo2nqLpH5#W>gnv*ySwSar('

psql -h whatsapp-postgres-development.cyd40iccy9uu.us-east-1.rds.amazonaws.com -p 5432 -U postgres -d whatsapp_business_development -f backend/migrations/complete_schema.sql
