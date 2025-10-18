package com.waynehe.wstorage.data.repository

import com.waynehe.wstorage.data.model.InventoryEntry
import kotlinx.coroutines.flow.StateFlow

interface InventoryRepository {
    val entries: StateFlow<Map<String, InventoryEntry>>

    suspend fun setCounts(cardId: String, ownedCount: Int, wishlistCount: Int)
    suspend fun incrementOwned(cardId: String)
    suspend fun decrementOwned(cardId: String)
    suspend fun incrementWishlist(cardId: String)
    suspend fun decrementWishlist(cardId: String)

    /**
     * Reserved synchronization hook for future cloud backends.
     * Implementations can perform best-effort upload/download when appropriate.
     */
    suspend fun syncWithRemote()
}
