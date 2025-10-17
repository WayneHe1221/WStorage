package com.waynehe.wstorage.data.repository

import com.waynehe.wstorage.data.model.CardDataBundle
import com.waynehe.wstorage.data.model.CardPage
import com.waynehe.wstorage.data.model.Rarity
import com.waynehe.wstorage.data.model.WsCard
import com.waynehe.wstorage.data.model.WsSeries
import kotlinx.serialization.SerializationException
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
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
                val bundle = json.decodeFromString<CardDataBundle>(rawJson)
                if (bundle.series.isNotEmpty() || bundle.cards.isNotEmpty()) {
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
                id = "sao-10th",
                name = "Sword Art Online 10th Anniversary",
                setCode = "SAO/S100",
                releaseYear = 2023
            ),
            WsSeries(
                id = "hololive-vol2",
                name = "hololive production Vol.2",
                setCode = "HOL/WE36",
                releaseYear = 2024
            ),
            WsSeries(
                id = "blue-archive",
                name = "Blue Archive",
                setCode = "BA/WE31",
                releaseYear = 2024
            )
        )

        private val defaultCards = listOf(
            WsCard(
                id = "sao-10th-001",
                seriesId = "sao-10th",
                cardCode = "SAO/S100-001",
                title = "Dual Wielder, Kirito",
                rarity = Rarity.SUPER_RARE,
                description = "Protagonist of SAO with dual wielding ability.",
                color = "BLACK",
                level = 3,
                cost = 2,
                imageUrl = null
            ),
            WsCard(
                id = "sao-10th-002",
                seriesId = "sao-10th",
                cardCode = "SAO/S100-002",
                title = "Flash of the Blue, Asuna",
                rarity = Rarity.RARE,
                description = "Asuna ready to support the front lines.",
                color = "BLUE",
                level = 2,
                cost = 1,
                imageUrl = null
            ),
            WsCard(
                id = "holo-vol2-001",
                seriesId = "hololive-vol2",
                cardCode = "HOL/WE36-001",
                title = "Secret Society holoX, La+ Darknesss",
                rarity = Rarity.SPECIAL,
                description = "The leader of holoX makes a mysterious entrance.",
                color = "PURPLE",
                level = 3,
                cost = 2,
                imageUrl = null
            ),
            WsCard(
                id = "holo-vol2-002",
                seriesId = "hololive-vol2",
                cardCode = "HOL/WE36-002",
                title = "Idol of the Stars, Hoshimachi Suisei",
                rarity = Rarity.SUPER_RARE,
                description = "Suisei sings with a shining stage presence.",
                color = "BLUE",
                level = 3,
                cost = 2,
                imageUrl = null
            ),
            WsCard(
                id = "ba-001",
                seriesId = "blue-archive",
                cardCode = "BA/WE31-001",
                title = "Gourmet Research, Yuuka",
                rarity = Rarity.UNCOMMON,
                description = "The meticulous treasurer of the Gourmet Research Club.",
                color = "YELLOW",
                level = 1,
                cost = 0,
                imageUrl = null
            ),
            WsCard(
                id = "ba-002",
                seriesId = "blue-archive",
                cardCode = "BA/WE31-002",
                title = "After-School Sweets Club, Azusa",
                rarity = Rarity.SUPER_RARE,
                description = "Azusa enjoys desserts after missions.",
                color = "RED",
                level = 2,
                cost = 2,
                imageUrl = null
            ),
            WsCard(
                id = "ba-003",
                seriesId = "blue-archive",
                cardCode = "BA/WE31-003",
                title = "On-the-Job Spirit, Aru",
                rarity = Rarity.RARE,
                description = "Aru brings energy to the Problem Solver 68 squad.",
                color = "GREEN",
                level = 1,
                cost = 1,
                imageUrl = null
            )
        )
    }
}
