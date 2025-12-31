import com.cloudbees.plugins.credentials.CredentialsProvider
import com.cloudbees.plugins.credentials.CredentialsScope
import com.cloudbees.plugins.credentials.domains.Domain
import com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl
import hudson.util.Secret
import jenkins.model.Jenkins
import org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl

def jenkins = Jenkins.get()
def domain = Domain.global()
def store = jenkins.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()

// 建立測試用 credentials
def credentials = []

// 1. Username/Password credential
credentials << new UsernamePasswordCredentialsImpl(
    CredentialsScope.GLOBAL,
    "test-credential-1",
    "Test username/password credential",
    "test-user",
    "test-password"
)

// 2. Secret text credential
credentials << new StringCredentialsImpl(
    CredentialsScope.GLOBAL,
    "test-credential-2",
    "Test secret text credential",
    Secret.fromString("test-secret-value")
)

// 3. Another username/password for variety
credentials << new UsernamePasswordCredentialsImpl(
    CredentialsScope.GLOBAL,
    "test-credential-3",
    "Another test credential",
    "admin-user",
    "admin-password"
)

// 新增 credentials
credentials.each { cred ->
    // 檢查是否已存在
    def existing = CredentialsProvider.lookupCredentials(
        cred.class,
        jenkins,
        null,
        null
    ).find { it.id == cred.id }

    if (existing == null) {
        store.addCredentials(domain, cred)
        println "Created credential: ${cred.id}"
    } else {
        println "Credential already exists: ${cred.id}"
    }
}

jenkins.save()
println "Test credentials setup completed"

// 驗證：列出所有 credentials
println "\n=== Verification ==="
def allCreds = CredentialsProvider.lookupCredentials(
    com.cloudbees.plugins.credentials.Credentials.class,
    jenkins,
    null,
    null
)
println "Total credentials count: ${allCreds.size()}"
allCreds.each { cred ->
    println "  - ${cred.id} (${cred.class.simpleName})"
}
