package com.waynehe.wstorage.data.repository

internal expect object CardResourceReader {
    fun readText(resourcePath: String): String?
}
