## Run alembic miegrations

## configs


```bash
cp alembic.example.ini alembic.ini
```

-Update 'alembic.ini' with your db ('sqlalchemy.url')

### (optional) Create a new migration
```bash
alembic revision --autogenerate -m "type your message"
```

### Upgrade the database
```bash
alembic upgrade head
```