# ── Stage 1: Build ────────────────────────────────────────────
FROM maven:3.9-eclipse-temurin-21-alpine AS build
WORKDIR /app

# Cache dependencies separately — only re-fetched when pom.xml changes
COPY pom.xml .
RUN mvn dependency:go-offline -q

# Build the fat JAR
# -DskipTests        — tests run locally, not in Docker
# -Dskip.frontend    — frontend is pre-built; static files already in src/main/resources/static/
COPY src ./src
RUN mvn package -DskipTests -Dskip.frontend=true -q

# ── Stage 2: Run ──────────────────────────────────────────────
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app

COPY --from=build /app/target/sat-engine.jar app.jar

EXPOSE 8080

# SPRING_PROFILES_ACTIVE can be overridden per platform (railway / render / local).
# Default: railway so existing Railway deploy is unaffected.
ENV SPRING_PROFILES_ACTIVE=railway
ENTRYPOINT java -Dspring.profiles.active=${SPRING_PROFILES_ACTIVE} -jar app.jar
