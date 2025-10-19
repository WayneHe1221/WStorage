package com.waynehe.wstorage.data.repository

import com.waynehe.wstorage.data.model.CardDataBundle
import com.waynehe.wstorage.data.model.CardPage
import com.waynehe.wstorage.data.model.Rarity
import com.waynehe.wstorage.data.model.WsCard
import com.waynehe.wstorage.data.model.WsSeries
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.contentOrNull
import kotlin.math.min

class InMemoryCardRepository(
    private val resourcePath: String = DEFAULT_RESOURCE_PATH,
    private val json: Json = defaultJson
) : CardRepository {

    private val cachedData: CardData by lazy { loadCardData() }

    override fun getAllSeries(): List<WsSeries> = cachedData.series.sortedBy { it.name }

    override fun getCardsBySeries(seriesId: String, page: Int, pageSize: Int): CardPage {
        val filtered = cachedData.cards.filter { it.seriesId == seriesId }
        return buildPage(filtered, page, pageSize)
    }

    override fun searchCards(keyword: String, page: Int, pageSize: Int): CardPage {
        if (keyword.isBlank()) {
            return CardPage(emptyList(), page, pageSize, totalCount = 0, hasMore = false)
        }
        val normalizedKeyword = keyword.trim().lowercase()
        val filtered = cachedData.cards.filter { card ->
            card.title.lowercase().contains(normalizedKeyword) ||
                card.cardCode.lowercase().contains(normalizedKeyword)
        }
        return buildPage(filtered, page, pageSize)
    }

    private fun buildPage(source: List<WsCard>, page: Int, pageSize: Int): CardPage {
        require(page >= 0) { "page must be greater than or equal to 0" }
        require(pageSize > 0) { "pageSize must be greater than 0" }

        if (source.isEmpty()) {
            return CardPage(emptyList(), page, pageSize, totalCount = 0, hasMore = false)
        }

        val fromIndex = page * pageSize
        if (fromIndex >= source.size) {
            return CardPage(emptyList(), page, pageSize, totalCount = source.size, hasMore = false)
        }

        val toIndex = min(fromIndex + pageSize, source.size)
        val items = source.subList(fromIndex, toIndex)
        val hasMore = toIndex < source.size
        return CardPage(items, page, pageSize, totalCount = source.size, hasMore = hasMore)
    }

    private fun loadCardData(): CardData {
        val rawJson = CardResourceReader.readText(resourcePath)
            ?: throw IllegalStateException("Card data resource $resourcePath not found")
        try {
            val bundle = parseCardBundle(rawJson)
                ?: throw IllegalStateException("Card data bundle is empty")
            if (bundle.series.isEmpty()) {
                throw IllegalStateException("Card data bundle does not include any series entries")
            }
            if (bundle.cards.isEmpty()) {
                throw IllegalStateException("Card data bundle does not include any card entries")
            }
            return CardData(bundle.series, bundle.cards)
        } catch (error: SerializationException) {
            throw IllegalStateException("Failed to parse card data", error)
        }
    }

    private fun parseCardBundle(rawJson: String): CardDataBundle? {
        val root = json.parseToJsonElement(rawJson)
        val obj = root as? JsonObject ?: return null
        val series = obj.safeArray("series")?.mapNotNull(::parseSeries).orEmpty()
        val cards = obj.safeArray("cards")?.mapNotNull(::parseCard).orEmpty()
        return CardDataBundle(series, cards)
    }

    private fun parseSeries(element: JsonElement): WsSeries? {
        val obj = element as? JsonObject ?: return null
        val id = obj.string("id") ?: return null
        val name = obj.string("name") ?: return null
        val setCode = obj.string("setCode") ?: return null
        val releaseYear = obj.int("releaseYear") ?: return null
        return WsSeries(id, name, setCode, releaseYear)
    }

    private fun parseCard(element: JsonElement): WsCard? {
        val obj = element as? JsonObject ?: return null
        val id = obj.string("id") ?: return null
        val seriesId = obj.string("seriesId") ?: return null
        val cardCode = obj.string("cardCode") ?: return null
        val title = obj.string("title") ?: return null
        val rarityCode = obj.string("rarity") ?: return null
        val rarity = Rarity.fromCode(rarityCode) ?: return null
        val description = obj.string("description") ?: ""
        val color = obj.string("color")?.ifBlank { null }
        val level = obj.int("level")
        val cost = obj.int("cost")
        val imageUrl = obj.string("imageUrl")?.ifBlank { null }
        val ownedCount = obj.int("ownedCount") ?: 0
        val wishlistCount = obj.int("wishlistCount") ?: 0
        return WsCard(
            id = id,
            seriesId = seriesId,
            cardCode = cardCode,
            title = title,
            rarity = rarity,
            description = description,
            color = color,
            level = level,
            cost = cost,
            imageUrl = imageUrl,
            ownedCount = ownedCount,
            wishlistCount = wishlistCount
        )
    }

    private fun JsonObject.safeArray(key: String): JsonArray? = (this[key] as? JsonArray)

    private fun JsonObject.string(key: String): String? = (this[key] as? JsonPrimitive)?.contentOrNull

    private fun JsonObject.int(key: String): Int? = (this[key] as? JsonPrimitive)?.intOrNull

    private data class CardData(
        val series: List<WsSeries>,
        val cards: List<WsCard>
    )

    companion object {
        private const val DEFAULT_RESOURCE_PATH = "cards.json"

        private val defaultJson = Json {
            ignoreUnknownKeys = true
        }
    }
}
