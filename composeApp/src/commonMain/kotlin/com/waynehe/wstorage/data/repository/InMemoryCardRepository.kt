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
    private val json: Json = defaultJson,
    private val fallbackSeries: List<WsSeries> = defaultSeries,
    private val fallbackCards: List<WsCard> = defaultCards
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
        if (rawJson != null) {
            try {
                val bundle = parseCardBundle(rawJson)
                if (bundle != null && (bundle.series.isNotEmpty() || bundle.cards.isNotEmpty())) {
                    val series = if (bundle.series.isNotEmpty()) bundle.series else fallbackSeries
                    val cards = if (bundle.cards.isNotEmpty()) bundle.cards else fallbackCards
                    return CardData(series, cards)
                }
            } catch (error: SerializationException) {
                // Ignore malformed JSON and use the fallback data below.
            } catch (error: IllegalArgumentException) {
                // Ignore and fall back to embedded data.
            }
        }
        return CardData(fallbackSeries, fallbackCards)
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

        private val defaultSeries = listOf(
            WsSeries(
                id = "ddd-s97",
                name = "The Detective Is Already Dead",
                setCode = "DDD/S97",
                releaseYear = 2021
            ),
            WsSeries(
                id = "sfn-s108",
                name = "Saekano the Movie: Finale",
                setCode = "SFN/S108",
                releaseYear = 2022
            )
        )

        private val defaultCards = listOf(
            WsCard(
                id = "ddd-s97-001",
                seriesId = "ddd-s97",
                cardCode = "DDD/S97-001",
                title = "Legendary Detective, Siesta",
                rarity = Rarity.SUPER_RARE,
                description = "Siesta fearlessly confronts the case with perfect composure.",
                color = "BLUE",
                level = 3,
                cost = 2,
                imageUrl = "https://ws-tcg.com/wp/wp-content/cardlist/cardimages/DDD/S97/DDD-S97-001.png"
            ),
            WsCard(
                id = "ddd-s97-002",
                seriesId = "ddd-s97",
                cardCode = "DDD/S97-002",
                title = "Reluctant Sidekick, Kimihiko",
                rarity = Rarity.RARE,
                description = "Kimihiko is pulled back onto the stage of adventure.",
                color = "YELLOW",
                level = 1,
                cost = 1,
                imageUrl = "https://ws-tcg.com/wp/wp-content/cardlist/cardimages/DDD/S97/DDD-S97-002.png"
            ),
            WsCard(
                id = "ddd-s97-003",
                seriesId = "ddd-s97",
                cardCode = "DDD/S97-003",
                title = "Energetic Assistant, Nagisa",
                rarity = Rarity.UNCOMMON,
                description = "Nagisa keeps spirits high for the new detective team.",
                color = "GREEN",
                level = 0,
                cost = 0,
                imageUrl = "https://ws-tcg.com/wp/wp-content/cardlist/cardimages/DDD/S97/DDD-S97-003.png"
            ),
            WsCard(
                id = "ddd-s97-004",
                seriesId = "ddd-s97",
                cardCode = "DDD/S97-004",
                title = "Mysterious Idol, Yui",
                rarity = Rarity.SUPER_RARE,
                description = "Yui steps onto the stage with a secret mission.",
                color = "RED",
                level = 2,
                cost = 1,
                imageUrl = "https://ws-tcg.com/wp/wp-content/cardlist/cardimages/DDD/S97/DDD-S97-004.png"
            ),
            WsCard(
                id = "ddd-s97-005",
                seriesId = "ddd-s97",
                cardCode = "DDD/S97-005",
                title = "Shadow Operative, Hel",
                rarity = Rarity.SUPER_RARE,
                description = "Hel manipulates events from the darkness.",
                color = "BLUE",
                level = 2,
                cost = 2,
                imageUrl = "https://ws-tcg.com/wp/wp-content/cardlist/cardimages/DDD/S97/DDD-S97-005.png"
            ),
            WsCard(
                id = "ddd-s97-006",
                seriesId = "ddd-s97",
                cardCode = "DDD/S97-006",
                title = "Tactical Support, Char",
                rarity = Rarity.UNCOMMON,
                description = "Char keeps the team coordinated from behind the scenes.",
                color = "YELLOW",
                level = 1,
                cost = 0,
                imageUrl = "https://ws-tcg.com/wp/wp-content/cardlist/cardimages/DDD/S97/DDD-S97-006.png"
            ),
            WsCard(
                id = "sfn-s108-001",
                seriesId = "sfn-s108",
                cardCode = "SFN/S108-001",
                title = "Producer in Everyday Clothes, Megumi",
                rarity = Rarity.RARE,
                description = "Megumi coordinates Blessing Software with gentle resolve.",
                color = "BLUE",
                level = 1,
                cost = 0,
                imageUrl = "https://ws-tcg.com/wp/wp-content/cardlist/cardimages/SFN/S108/SFN-S108-001.png"
            ),
            WsCard(
                id = "sfn-s108-002",
                seriesId = "sfn-s108",
                cardCode = "SFN/S108-002",
                title = "Scenario Rewrite, Utaha",
                rarity = Rarity.SUPER_RARE,
                description = "Utaha polishes the screenplay with unwavering confidence.",
                color = "RED",
                level = 3,
                cost = 2,
                imageUrl = "https://ws-tcg.com/wp/wp-content/cardlist/cardimages/SFN/S108/SFN-S108-002.png"
            ),
            WsCard(
                id = "sfn-s108-003",
                seriesId = "sfn-s108",
                cardCode = "SFN/S108-003",
                title = "Illustrator's Determination, Eriri",
                rarity = Rarity.SUPER_RARE,
                description = "Eriri stays up all night refining her key visuals.",
                color = "YELLOW",
                level = 2,
                cost = 2,
                imageUrl = "https://ws-tcg.com/wp/wp-content/cardlist/cardimages/SFN/S108/SFN-S108-003.png"
            ),
            WsCard(
                id = "sfn-s108-004",
                seriesId = "sfn-s108",
                cardCode = "SFN/S108-004",
                title = "Stage Performer, Michiru",
                rarity = Rarity.UNCOMMON,
                description = "Michiru livens up the party with her guitar riffs.",
                color = "GREEN",
                level = 1,
                cost = 1,
                imageUrl = "https://ws-tcg.com/wp/wp-content/cardlist/cardimages/SFN/S108/SFN-S108-004.png"
            ),
            WsCard(
                id = "sfn-s108-005",
                seriesId = "sfn-s108",
                cardCode = "SFN/S108-005",
                title = "Return of the Rival, Izumi",
                rarity = Rarity.UNCOMMON,
                description = "Izumi brings fresh competition to Megumi's plans.",
                color = "BLUE",
                level = 0,
                cost = 0,
                imageUrl = "https://ws-tcg.com/wp/wp-content/cardlist/cardimages/SFN/S108/SFN-S108-005.png"
            ),
            WsCard(
                id = "sfn-s108-006",
                seriesId = "sfn-s108",
                cardCode = "SFN/S108-006",
                title = "Blessing Software's Future, Megumi",
                rarity = Rarity.SPECIAL,
                description = "Megumi smiles toward the finished movie project.",
                color = "BLUE",
                level = 3,
                cost = 2,
                imageUrl = "https://ws-tcg.com/wp/wp-content/cardlist/cardimages/SFN/S108/SFN-S108-006.png"
            )
        )
    }
}
