FROM sergeyboyko/qtum:19.1

RUN apt-get update && apt-get install -y sudo python python3.7 python3-pip ca-certificates curl wget apt-utils

RUN rm -rf /data
RUN mkdir /data && mkdir /data/bin
RUN cp /usr/local/bin/qtumd /usr/local/bin/qtum-cli /data/bin

VOLUME ["/data"]
ENV HOME /data
ENV ALLOW_ROOT 1
WORKDIR /data

# daemon port
EXPOSE 7000

COPY start.sh /data/
COPY start_regtest.py /data/
CMD ./start.sh

