pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "card-extractor"

// :core is pure JVM (model + OCR parser) and builds anywhere with a JDK —
// CI and headless environments run `gradle :core:test` without the Android SDK.
include(":core")

// :app needs the Android SDK; include it only where one is configured
// (Android Studio writes local.properties automatically).
val hasAndroidSdk =
    System.getenv("ANDROID_HOME") != null ||
        System.getenv("ANDROID_SDK_ROOT") != null ||
        (rootDir.resolve("local.properties").takeIf { it.isFile }
            ?.readLines()?.any { it.trim().startsWith("sdk.dir") } == true)

// CI runners often carry an SDK but only need the JVM parser tests.
val coreOnly = System.getenv("CARDX_CORE_ONLY") == "1"

if (hasAndroidSdk && !coreOnly) {
    include(":app")
} else {
    println("NOTE: Android SDK not found -> :app module skipped (only :core is active).")
}
