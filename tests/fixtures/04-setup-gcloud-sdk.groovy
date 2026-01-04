import jenkins.model.Jenkins
import hudson.tools.ToolProperty
import com.cloudbees.jenkins.plugins.gcloudsdk.GCloudInstallation

// Setup Google Cloud SDK installation

def jenkinsInstance = Jenkins.getInstance()
def descriptor = jenkinsInstance.getDescriptor(GCloudInstallation.class)

// Check current installations
def currentInstallations = descriptor.getInstallations()
println "Current GCloud SDK installations: ${currentInstallations.length}"

// Define the installation
def installationName = "Default"
def gcloudHome = "/usr"  // gcloud is at /usr/bin/gcloud

// Check if installation already exists
def existingInstallation = currentInstallations.find { it.name == installationName }

if (existingInstallation == null) {
    // Create new installation with empty properties (manual installation, not auto-installer)
    def installation = new GCloudInstallation(
        installationName,
        gcloudHome,
        [] as List<ToolProperty<?>>
    )

    // Set the installations
    descriptor.setInstallations(installation)
    descriptor.save()

    println "Created GCloud SDK installation: ${installationName}"
    println "  Home: ${gcloudHome}"
} else {
    println "GCloud SDK installation already exists: ${installationName}"
    println "  Home: ${existingInstallation.home}"
}

// Verify the installation
def updatedInstallations = descriptor.getInstallations()
println "\n=== Verification ==="
println "Total GCloud SDK installations: ${updatedInstallations.length}"
updatedInstallations.each { inst ->
    println "  - ${inst.name}: ${inst.home}"
}
