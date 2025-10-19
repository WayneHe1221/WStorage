package com.waynehe.wstorage.data.repository

import android.app.Application

internal actual object CardResourceReader {
    actual fun readText(resourcePath: String): String? {
        val loader = InMemoryCardRepository::class.java.classLoader
        val stream = loader?.getResourceAsStream(resourcePath)
        if (stream != null) {
            return stream.bufferedReader().use { it.readText() }
        }

        val application = currentApplication() ?: return null
        return runCatching {
            application.assets.open(resourcePath).bufferedReader().use { it.readText() }
        }.getOrNull()
    }

    private fun currentApplication(): Application? {
        return try {
            val activityThreadClass = Class.forName("android.app.ActivityThread")
            val currentApplicationMethod = activityThreadClass.getMethod("currentApplication")
            (currentApplicationMethod.invoke(null) as? Application)
                ?: run {
                    val appGlobalsClass = Class.forName("android.app.AppGlobals")
                    val getInitialApplication = appGlobalsClass.getMethod("getInitialApplication")
                    getInitialApplication.invoke(null) as? Application
                }
        } catch (_: Throwable) {
            null
        }
    }
}
