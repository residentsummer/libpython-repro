FROM phusion/baseimage:jammy-1.0.1

ENV TERM=xterm LANG=en_US.UTF-8 DEBIAN_FRONTEND=noninteractive

COPY requirements.txt /tmp/
RUN apt-get update && \
    apt-get -y -q install --no-install-recommends \
             build-essential \
             python3-dev \
             python3-pip \
             openjdk-17-jdk-headless \
             rlwrap \
             git && \
    pip install -r /tmp/requirements.txt && \
    apt-get -y autoremove --purge \
             build-essential \
             python3-dev && \
    apt-get clean all && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# install clojure cli
RUN cd /tmp && \
    curl -L -O https://github.com/clojure/brew-install/releases/latest/download/linux-install.sh && \
    chmod +x ./linux-install.sh && \
    ./linux-install.sh && \
    rm -rf /tmp/* /var/tmp/*

RUN mkdir -p /var/www
COPY deps.edn /var/www/deps.edn
# cache java/clojure deps
RUN cd /var/www && \
    clojure -P -T:bootstrap && \
    clojure -P -Arepl:dev

ENV PYTHONPATH /var/www/:$PYTHON_PATH
ENV PYTHONDONTWRITEBYTECODE 1

COPY cljbridge /var/www/cljbridge
COPY core /var/www/core
COPY clj /var/www/clj
