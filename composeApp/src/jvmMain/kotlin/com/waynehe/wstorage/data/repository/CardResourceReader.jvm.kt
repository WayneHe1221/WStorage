package com.waynehe.wstorage.data.repository

internal actual object CardResourceReader {
    actual fun readText(resourcePath: String): String? {
        val loader = InMemoryCardRepository::class.java.classLoader ?: return null
        return loader.getResourceAsStream(resourcePath)?.bufferedReader()?.use { it.readText() }
    }
}
