import hudson.security.FullControlOnceLoggedInAuthorizationStrategy
import hudson.security.HudsonPrivateSecurityRealm
import jenkins.model.Jenkins
import jenkins.security.ApiTokenProperty

def jenkins = Jenkins.get()
def realm = new HudsonPrivateSecurityRealm(false)

def username = "jenkins-test"
def password = "test-password-for-jenkins-inspector"
def user = realm.createAccount(username, password)

jenkins.setSecurityRealm(realm)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
jenkins.setAuthorizationStrategy(strategy)

def apiTokenProperty = user.getProperty(ApiTokenProperty.class)
if (apiTokenProperty == null) {
    apiTokenProperty = new ApiTokenProperty()
    user.addProperty(apiTokenProperty)
}

def tokenStore = apiTokenProperty.tokenStore
def tokenName = "test-token-for-jenkins-inspector"
def tokenValue = "1100000000000000000000000000000000"

def existingToken = tokenStore.tokenList.find { it.name == tokenName }
if (existingToken == null) {
    // Jenkins 2.5xx 起 addFixedNewToken 多了第三個過期日參數；null 代表永不過期
    tokenStore.addFixedNewToken(tokenName, tokenValue, null)
}

user.save()
jenkins.save()
