package com.waynehe.wstorage.data.repository

import com.russhwolf.settings.Settings
import com.waynehe.wstorage.data.model.InventoryEntry
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.Json

class SettingsInventoryRepository(
    private val settings: Settings,
    private val dispatcher: CoroutineDispatcher = Dispatchers.Default,
    private val json: Json = Json { ignoreUnknownKeys = true }
) : InventoryRepository {

    private val mutex = Mutex()
    private val _entries = MutableStateFlow<Map<String, InventoryEntry>>(emptyMap())

    override val entries: StateFlow<Map<String, InventoryEntry>> = _entries.asStateFlow()

    init {
        _entries.value = readFromStorage()
    }

    override suspend fun setCounts(cardId: String, ownedCount: Int, wishlistCount: Int) {
        val entry = InventoryEntry(cardId, ownedCount, wishlistCount)
        writeEntry(entry)
    }

    override suspend fun incrementOwned(cardId: String) {
        adjustEntry(cardId) { it.copy(ownedCount = it.ownedCount + 1) }
    }

    override suspend fun decrementOwned(cardId: String) {
        adjustEntry(cardId) { it.copy(ownedCount = (it.ownedCount - 1).coerceAtLeast(0)) }
    }

    override suspend fun incrementWishlist(cardId: String) {
        adjustEntry(cardId) { it.copy(wishlistCount = it.wishlistCount + 1) }
    }

    override suspend fun decrementWishlist(cardId: String) {
        adjustEntry(cardId) { it.copy(wishlistCount = (it.wishlistCount - 1).coerceAtLeast(0)) }
    }

    override suspend fun syncWithRemote() {
        // Reserved for future cloud sync implementation.
    }

    private suspend fun writeEntry(entry: InventoryEntry) {
        val sanitized = entry.sanitized()
        val snapshot = mutex.withLock {
            val mutable = _entries.value.toMutableMap()
            if (sanitized.ownedCount == 0 && sanitized.wishlistCount == 0) {
                mutable.remove(entry.cardId)
            } else {
                mutable[entry.cardId] = sanitized
            }
            mutable.toMap().also { _entries.value = it }
        }
        persist(snapshot)
    }

    private suspend fun adjustEntry(cardId: String, transform: (InventoryEntry) -> InventoryEntry) {
        val snapshot = mutex.withLock {
            val currentEntries = _entries.value
            val base = currentEntries[cardId] ?: InventoryEntry(cardId)
            val updated = transform(base).sanitized()
            val mutable = currentEntries.toMutableMap()
            if (updated.ownedCount == 0 && updated.wishlistCount == 0) {
                mutable.remove(cardId)
            } else {
                mutable[cardId] = updated
            }
            mutable.toMap().also { _entries.value = it }
        }
        persist(snapshot)
    }

    private suspend fun persist(entries: Map<String, InventoryEntry>) {
        val serializable = entries.values.map { it.sanitized() }
        withContext(dispatcher) {
            if (serializable.isEmpty()) {
                settings.remove(STORAGE_KEY)
            } else {
                val encoded = json.encodeToString(ListSerializer(InventoryEntry.serializer()), serializable)
                settings.putString(STORAGE_KEY, encoded)
            }
        }
    }

    private fun readFromStorage(): Map<String, InventoryEntry> {
        val raw = settings.getStringOrNull(STORAGE_KEY) ?: return emptyMap()
        return runCatching {
            val decoded = json.decodeFromString(ListSerializer(InventoryEntry.serializer()), raw)
            decoded.map { it.sanitized() }.associateBy { it.cardId }
        }.getOrDefault(emptyMap())
    }

    companion object {
        private const val STORAGE_KEY = "inventory.entries"
    }
}
