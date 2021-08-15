FROM ubuntu
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt update && apt install -y wget gnupg2 gstreamer1.0-libav pulseaudio python3 python3-pip \
    && wget -q -O - https://apt.mopidy.com/mopidy.gpg | apt-key add - \
    && wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/buster.list \
    && apt update && apt install -y mopidy \
    && pip install Mopidy-Mobile
RUN adduser myuser && chown myuser /home/myuser
COPY pulse-client.conf /etc/pulse/client.conf
COPY mopidy.conf /home/myuser/.config/mopidy/mopidy.conf
EXPOSE 6680
USER myuser
CMD ["mopidy"]
