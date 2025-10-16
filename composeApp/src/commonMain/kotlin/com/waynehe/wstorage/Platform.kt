package com.waynehe.wstorage

interface Platform {
    val name: String
}

expect fun getPlatform(): Platform