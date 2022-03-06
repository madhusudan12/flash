# flash

## Prerequisites
Docker to be installed in the machine that you are running this

## Getting Service up and running

### Clone Repo
```
git clone git@github.com:madhusudan12/flash.git
```

### Populate config

`flash/config.py`

```
SECRET_KEY = "" # give secret value
SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://db_user:db_password#@db_endpoint/flash"
SQLALCHEMY_TRACK_MODIFICATIONS = True
UPLOAD_FOLDER = "./uploads"
```

### bring up the container

```
cd flash
docker-compose up --build
```

Now the app is up, you can hit the API's
