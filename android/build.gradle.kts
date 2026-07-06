// Root build file — plugins are declared per module via the version catalog.
tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
