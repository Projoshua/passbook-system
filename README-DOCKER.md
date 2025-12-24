
# ===========================================
# FILE: README-DOCKER.md
# ===========================================
# Docker Setup Instructions

## Prerequisites
- Docker installed (https://docs.docker.com/get-docker/)
- Docker Compose installed (usually comes with Docker Desktop)

## Quick Start

1. **Create the required files**:
   - Copy all file contents from above into their respective files
   - Make sure you have Dockerfile, docker-compose.yml, .env, and .dockerignore

2. **Configure your superuser credentials**:
   Edit the `.env` file and change these values:
   ```
   DJANGO_SUPERUSER_USERNAME=youradmin
   DJANGO_SUPERUSER_EMAIL=your@email.com
   DJANGO_SUPERUSER_PASSWORD=YourSecurePassword123!
   ```

3. **Build and start the containers**:
   ```bash
   docker-compose up --build
   ```

4. **Access the application**:
   - Django App: http://localhost:8000
   - MinIO Console: http://localhost:9001 (login: minioadmin/minioadmin)
   - PostgreSQL: localhost:5432

5. **Login to Django**:
   - Use the credentials you set in the `.env` file
   - The user will have sysadmin privileges

## Useful Commands

### Start containers (after first build)
```bash
docker-compose up
```

### Start containers in background
```bash
docker-compose up -d
```

### Stop containers
```bash
docker-compose down
```

### Stop containers and remove volumes (WARNING: deletes all data)
```bash
docker-compose down -v
```

### View logs
```bash
docker-compose logs -f web
```

### Run Django commands
```bash
docker-compose exec web python manage.py <command>
```

### Create additional users
```bash
# Create a regular user
docker-compose exec web python manage.py create_user \
  --username student1 \
  --email student1@example.com \
  --password password123 \
  --user_type student \
  --phone_number +256700000000

# Create another admin
docker-compose exec web python manage.py create_superuser \
  --username admin2 \
  --email admin2@example.com \
  --password password123
```

### Access Django shell
```bash
docker-compose exec web python manage.py shell
```

### Run migrations
```bash
docker-compose exec web python manage.py migrate
```

### Create new migrations
```bash
docker-compose exec web python manage.py makemigrations
```

### Access PostgreSQL
```bash
docker-compose exec db psql -U postgres -d postgres
```

## Troubleshooting

### Port already in use
If you get a port conflict error, you can change the ports in docker-compose.yml:
```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001 for Django
  - "5433:5432"  # Change 5432 to 5433 for PostgreSQL
```

### Superuser already exists
If the superuser already exists, the command will skip creation. To reset:
```bash
docker-compose exec web python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(username='admin').delete()
>>> exit()
```
Then restart the container.

### MinIO buckets not created
If MinIO buckets aren't created, run:
```bash
docker-compose up minio-setup
```

### Reset everything
```bash
docker-compose down -v
docker-compose up --build
```

## Production Deployment

For production, update these in your `.env`:
1. Set `DEBUG=False`
2. Generate a new `SECRET_KEY`
3. Set proper `ALLOWED_HOSTS`
4. Use strong passwords
5. Consider using a proper web server (Gunicorn + Nginx)

## File Structure
```
your-project/
├── docker-compose.yml
├── Dockerfile
├── .env
├── .dockerignore
├── requirements.txt
├── manage.py
├── AttendanceSystem/
│   ├── settings.py (updated with environment variables)
│   └── ...
├── accounts/
│   └── management/
│       └── commands/
│           ├── create_superuser.py
│           └── create_user.py
└── ...
```