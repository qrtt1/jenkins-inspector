ARG JENKINS_IMAGE=jenkins/jenkins:lts-jdk21
FROM ${JENKINS_IMAGE}

# 安裝必要的 plugins（不指定版本，讓 plugin-cli 自動選擇相容版本）
RUN jenkins-plugin-cli --plugins \
    credentials \
    plain-credentials \
    credentials-binding \
    google-oauth-plugin \
    gcloud-sdk \
    workflow-job \
    workflow-cps \
    workflow-basic-steps \
    workflow-durable-task-step

# 安裝 Google Cloud SDK
USER root
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    apt-get update && apt-get install -y google-cloud-cli && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 跳過初始設定精靈
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

USER jenkins
