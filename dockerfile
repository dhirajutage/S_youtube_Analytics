# Use the official Apache Airflow image as the base
FROM apache/airflow:2.6.0

# Switch to the root user
USER root

# Install Java 17
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk-headless wget procps && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME for OpenJDK 17
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64 
ENV PATH=$JAVA_HOME/bin:$PATH

# Download and set up Apache Spark 3.5.2 with Hadoop 3
ENV SPARK_VERSION=3.5.2
ENV HADOOP_VERSION=3
ENV SCALA_VERSION=2.12.18
ENV SPARK_HOME=/opt/spark

RUN cd /tmp && \
    wget --no-verbose https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz && \
    tar -xvzf spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz && \
    mv spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} $SPARK_HOME && \
    rm spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz

# Add Spark to the PATH
ENV PATH=$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH

# Download necessary jars for Spark and add to the Spark classpath
# RUN wget --no-verbose -P $SPARK_HOME/jars \
#     https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.5.2/iceberg-spark-runtime-3.5_2.12-1.5.2.jar && \
#     wget --no-verbose -P $SPARK_HOME/jars \
#     https://repo1.maven.org/maven2/org/projectnessie/nessie-integrations/nessie-spark-extensions-3.5_2.12/0.95.0/nessie-spark-extensions-3.5_2.12-0.95.0.jar && \
#     wget --no-verbose -P $SPARK_HOME/jars \
#     https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.20.131/bundle-2.20.131.jar && \
#     wget --no-verbose -P $SPARK_HOME/jars \
#     https://repo1.maven.org/maven2/software/amazon/awssdk/url-connection-client/2.20.131/url-connection-client-2.20.131.jar && \
#     wget --no-verbose -P $SPARK_HOME/jars \
#     https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.1/hadoop-aws-3.3.1.jar

# Switch back to the airflow user
USER airflow

# Install any Python dependencies (if needed)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
