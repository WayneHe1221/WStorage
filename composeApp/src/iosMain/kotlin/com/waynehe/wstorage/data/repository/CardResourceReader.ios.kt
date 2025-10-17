package com.waynehe.wstorage.data.repository

import platform.Foundation.NSBundle
import platform.Foundation.NSData
import platform.Foundation.NSString
import platform.Foundation.NSUTF8StringEncoding
import platform.Foundation.create

internal actual object CardResourceReader {
    actual fun readText(resourcePath: String): String? {
        val components = resourcePath.split('.', limit = 2)
        val resourceName = components.firstOrNull() ?: return null
        val resourceExtension = components.getOrNull(1)
        val path = NSBundle.mainBundle.pathForResource(resourceName, resourceExtension) ?: return null
        val data = NSData.create(contentsOfFile = path) ?: return null
        val string = NSString.create(data = data, encoding = NSUTF8StringEncoding)
        return string as String?
    }
}
