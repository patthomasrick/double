FROM --platform=linux/amd64 ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/home/ubuntu

# Install Docker CLI.
RUN apt-get update && apt-get install -y ca-certificates curl gnupg lsb-release && mkdir -m 0755 -p /etc/apt/keyrings && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list >/dev/null
RUN apt-get update && apt-get -fy install docker-ce-cli

# Override Python.
COPY bin/* /overrides/bin/

# Path.
ENV PATH=/overrides/bin:$PATH

# CMD - just wait forever
CMD ["tail", "-f", "/dev/null"]
