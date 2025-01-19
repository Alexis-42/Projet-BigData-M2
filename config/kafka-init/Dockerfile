FROM confluentinc/cp-kafka:latest

# Create a directory for logs with proper permissions
RUN mkdir -p /tmp/kafka-logs && \
    chmod -R 777 /tmp/kafka-logs

# Set log directory environment variable
ENV LOG_DIR=/tmp/kafka-logs

COPY --chmod=0755 init-kafka.sh /init-kafka.sh
CMD ["/init-kafka.sh"]