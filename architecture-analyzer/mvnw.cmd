@ECHO OFF
SETLOCAL
SET MVNW_DIR=%~dp0
SET MAVEN_VERSION=3.9.9
SET MAVEN_HOME=%MVNW_DIR%.mvn\apache-maven-%MAVEN_VERSION%
IF NOT EXIST "%MAVEN_HOME%\bin\mvn.cmd" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing 'https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/%MAVEN_VERSION%/apache-maven-%MAVEN_VERSION%-bin.zip' -OutFile '%MVNW_DIR%.mvn\apache-maven.zip'; Expand-Archive -Force '%MVNW_DIR%.mvn\apache-maven.zip' '%MVNW_DIR%.mvn'"
)
CALL "%MAVEN_HOME%\bin\mvn.cmd" %*
ENDLOCAL
