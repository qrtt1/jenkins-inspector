FROM jenkins/jenkins:lts-jdk17

# 安裝必要的 plugins（不指定版本，讓 plugin-cli 自動選擇相容版本）
RUN jenkins-plugin-cli --plugins \
    credentials \
    plain-credentials \
    credentials-binding

# 跳過初始設定精靈
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

USER jenkins
