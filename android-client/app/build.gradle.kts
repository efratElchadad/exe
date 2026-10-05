plugins { id("com.android.application") }
android {
 namespace = "com.androidcompiler.mobile"
 compileSdk = 35
 defaultConfig {
  applicationId = "com.androidcompiler.mobile"
  minSdk = 26
  targetSdk = 35
  versionCode = 60
  versionName = "0.6.0-preview"
  testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
 }
 compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
}
dependencies {
 androidTestImplementation("androidx.test:runner:1.6.2")
 androidTestImplementation("androidx.test:core:1.6.1")
 androidTestImplementation("androidx.test.ext:junit:1.2.1")
}
