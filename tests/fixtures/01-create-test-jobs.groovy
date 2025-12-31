import jenkins.model.Jenkins
import hudson.model.FreeStyleProject
import hudson.model.ListView
import hudson.tasks.Shell

def jenkins = Jenkins.get()

// 1. 建立根目錄的 Freestyle Jobs
def jobNames = ["test-job-1", "test-job-2", "test-job-3"]
jobNames.each { name ->
    if (jenkins.getItem(name) == null) {
        def job = jenkins.createProject(FreeStyleProject, name)
        println "Created job: ${name}"
    }
}

// 2. 建立 long-running-job（用於測試 stop-builds）
def longJobName = "long-running-job"
if (jenkins.getItem(longJobName) == null) {
    def longJob = jenkins.createProject(FreeStyleProject, longJobName)
    // 加入 shell script build step: sleep 60
    longJob.buildersList.add(new Shell("echo 'Starting long running job...'\nsleep 60\necho 'Job completed'"))
    longJob.save()
    println "Created job: ${longJobName} (with sleep 60)"
}

// 3. 建立測試用的 View 並加入 Jobs
def viewName = "test-view"
def view = jenkins.getView(viewName)
if (view == null) {
    view = new ListView(viewName, jenkins)
    jenkins.addView(view)
    println "Created view: ${viewName}"
}

// 將 test-job-1 和 test-job-2 加入 test-view
["test-job-1", "test-job-2"].each { jobName ->
    def job = jenkins.getItem(jobName)
    if (job != null && !view.contains(job)) {
        view.add(job)
        println "Added ${jobName} to ${viewName}"
    }
}

// 4. 建立另一個空的 View
def emptyViewName = "empty-view"
if (jenkins.getView(emptyViewName) == null) {
    def emptyView = new ListView(emptyViewName, jenkins)
    jenkins.addView(emptyView)
    println "Created empty view: ${emptyViewName}"
}

jenkins.save()
println "Test jobs and views setup completed"

// 驗證：檢查 test-job-3 不在任何自訂 view 中
println "\n=== Verification ==="
def job3 = jenkins.getItem("test-job-3")
def viewsContainingJob3 = jenkins.views.findAll { v ->
    // 排除 Jenkins 預設的 view（不區分大小寫）
    v.name.toLowerCase() != "all" && v.contains(job3)
}

if (viewsContainingJob3.isEmpty()) {
    println "✓ test-job-3 is not in any custom view (as expected)"
} else {
    println "✗ test-job-3 found in views: ${viewsContainingJob3.collect { it.name }}"
}

// 列出各 view 包含的 jobs
jenkins.views.each { v ->
    if (v.name.toLowerCase() != "all") {
        def jobs = v.items.collect { it.name }
        println "View '${v.name}' contains: ${jobs}"
    }
}