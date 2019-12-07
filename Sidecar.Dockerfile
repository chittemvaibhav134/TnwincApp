FROM amazonlinux:latest
RUN yum install awscli -y
COPY start.sh /
COPY import /import
ENTRYPOINT /start.sh