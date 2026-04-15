FROM eclipse-temurin:21-jdk

# Crear directorio de trabajo temporal
WORKDIR /build

# Instalar dependencias necesarias
RUN apt-get update && \
    apt-get install -y git wget && \
    apt-get clean

# Descargar BuildTools y compilar Spigot
RUN wget -O BuildTools.jar https://hub.spigotmc.org/jenkins/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar && \
    git config --global --unset core.autocrlf || true && \
    java -jar BuildTools.jar --rev 1.21.11 && \
    cp spigot-1.21.11.jar /spigot.jar && \
    rm -rf /build

# Crear carpeta final
WORKDIR /data

# Exponer puertos
EXPOSE 25565
EXPOSE 19132/udp

# Comando de inicio que copia el JAR a /data (volumen) y lo ejecuta
CMD ["sh", "-c", "cp /spigot.jar /data/spigot.jar && java -Xmx$MEMORY -Xms$MEMORY -jar /data/spigot.jar nogui"]
