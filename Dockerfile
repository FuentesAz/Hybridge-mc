FROM eclipse-temurin:25-jdk

WORKDIR /build

RUN apt-get update && \
    apt-get install -y git wget && \
    apt-get clean

ARG SPIGOT_VERSION=26.2

RUN wget -O BuildTools.jar https://hub.spigotmc.org/jenkins/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar && \
    git config --global --unset core.autocrlf || true && \
    java -jar BuildTools.jar --rev ${SPIGOT_VERSION} && \
    cp spigot-${SPIGOT_VERSION}.jar /spigot.jar && \
    rm -rf /build

WORKDIR /data

EXPOSE 25565
EXPOSE 19132/udp

CMD ["sh", "-c", "cp /spigot.jar /data/spigot.jar && java -Xmx$MEMORY -Xms$MEMORY -jar /data/spigot.jar nogui"]
