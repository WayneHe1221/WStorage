package com.waynehe.wstorage.data.repository

import com.waynehe.wstorage.data.model.CardPage
import com.waynehe.wstorage.data.model.WsSeries

/**
 * Provides read-only access to Weiss Schwarz card data.
 */
interface CardRepository {
    /**
     * Returns every available series. The result is sorted alphabetically by series name.
     */
    fun getAllSeries(): List<WsSeries>

    /**
     * Loads cards that belong to a particular series.
     * @param seriesId Unique identifier of the series.
     * @param page Zero-based page index.
     * @param pageSize Number of items per page.
     */
    fun getCardsBySeries(seriesId: String, page: Int, pageSize: Int): CardPage

    /**
     * Searches for cards whose title or card code contains the given keyword.
     * @param keyword Search term. Blank keywords return an empty result.
     * @param page Zero-based page index.
     * @param pageSize Number of items per page.
     */
    fun searchCards(keyword: String, page: Int, pageSize: Int): CardPage
}
