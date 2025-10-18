package com.waynehe.wstorage.data.model

import kotlinx.serialization.Serializable

@Serializable
data class InventoryEntry(
    val cardId: String,
    val ownedCount: Int = 0,
    val wishlistCount: Int = 0
) {
    fun sanitized(): InventoryEntry = copy(
        ownedCount = ownedCount.coerceAtLeast(0),
        wishlistCount = wishlistCount.coerceAtLeast(0)
    )
}
