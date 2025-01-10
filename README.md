# Project Setup Instructions

# 1. Clone the Repository
```
git clone git@gitlab.com:sph8610935/sph-media.git
cd sph-media
```

# 2. Build Custom Docker Images
## 2.1 Build the Custom Airflow Image

```
docker build -t custom-airflow-spark:latest .

```

## 2.2 Build the Custom Jupyter Spark Image

```
cd docker/Dockerfile
docker build -t custom-jupyter-spark:latest .

```

# 3. Set Up and Start Docker Services
## 3.1 Docker Compose

```
cd ..
docker-compose up -d

```

This command will:
Start PostgreSQL for Airflow metadata storage.
Start Spark Master and Worker containers.
Start MinIO for S3-compatible storage.
Start Dremio for querying and analysis.
Start Metabase for data visualization.
Start Airflow for orchestration.
Start Nessie for data catalog management.
Start Jupyter Notebook for interactive development.

# 4. Verify the Setup
## 4.1 Check Running Containers
To ensure all services are running, execute:

```
docker ps
```

## 4.2 Accessing Services

Airflow Web UI: http://localhost:8090
Spark Master UI: http://localhost:8080
Spark Worker UI: http://localhost:8081
MinIO Console: http://localhost:9001
Dremio UI: http://localhost:9047
Metabase UI: http://localhost:3000
Jupyter Notebook: http://localhost:8899
Nessie API: http://localhost:19120/api/v1

# 5. Managing the Environment
##5.1 Stopping Services
To stop all services:
```
docker-compose down

```
## 5.2 Restarting Services
To restart all services:
```
docker-compose up -d

```

# 6. Working with the Project
## 6.1 Airflow
Deploy DAGs: Place your DAG files in the dags directory. They will automatically be picked up by Airflow.
View Logs: Logs can be accessed in the logs directory or through the Airflow UI.
## 6.2 Jupyter Notebook
Running Notebooks: Access Jupyter via http://localhost:8899 and start working with Spark through notebooks.
## 6.3 MinIO
Access Files: Use the MinIO Console to manage your S3-compatible storage. Upload files to landing, curated, or reporting buckets as needed.
## 6.4 Supeset
Create Dashboards: Connection string to connect Apache Superset to Dremio
 ``` 
 docker inspect dremio get networks  # IP address of Dremio
 dremio+flight://username:password@ip_address_of_dremio:32010/?UseEncryption=false

 ```
## 6.5 Dremio

 if Dremio goes down restart with below docker command 

  ``` 
  docker run -d \
  --platform linux/amd64 \
  --name dremio \
  -p 9047:9047 \
  -e DREMIO_UID=0 \
  -e DREMIO_GID=0 \
  --network airflow_net \
  dremio/dremio-oss:latest
  


   ``` 
## 6.6 Connect Dremio to Nessie


  ``` 
For your access key, set “username”
For your secret key, set “password”
Set root path to “Minio Bucket” 
Set the following connection properties:
fs.s3a.path.style.access = true
fs.s3a.endpoint = minio:9000. #minio endpoint
dremio.s3.compat = true

  ``` 

# Use Apache Superset .Build Docker image using Below Github

   https://github.com/AlexMercedCoder/dremio-superset-docker-image/tree/main


