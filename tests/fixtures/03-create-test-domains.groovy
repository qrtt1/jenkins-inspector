import com.cloudbees.plugins.credentials.CredentialsScope
import com.cloudbees.plugins.credentials.SystemCredentialsProvider
import com.cloudbees.plugins.credentials.domains.Domain
import jenkins.model.Jenkins
import org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl
import hudson.util.Secret
import java.util.Collections

// Create test domains

def store = SystemCredentialsProvider.getInstance().getStore()

def domains = [
    [name: "staging", description: "Staging environment credentials"],
    [name: "production", description: "Production environment credentials"],
]

domains.each { domainDef ->
    def existing = store.getDomains().find { it.getName() == domainDef.name }
    if (existing == null) {
        def domain = new Domain(domainDef.name, domainDef.description, Collections.emptyList())
        store.addDomain(domain)
        println "Created domain: ${domainDef.name}"
    } else {
        println "Domain already exists: ${domainDef.name}"
    }
}

// Add a test credential into staging domain for count verification

def stagingDomain = store.getDomains().find { it.getName() == "staging" }
if (stagingDomain != null) {
    def existingCredential = store.getCredentials(stagingDomain).find { it.id == "staging-credential-1" }
    if (existingCredential == null) {
        def credential = new StringCredentialsImpl(
            CredentialsScope.GLOBAL,
            "staging-credential-1",
            "Staging domain test credential",
            Secret.fromString("staging-secret-value")
        )
        store.addCredentials(stagingDomain, credential)
        println "Created credential: staging-credential-1"
    } else {
        println "Credential already exists: staging-credential-1"
    }
}

Jenkins.instance.save()
println "Test domains setup completed"
