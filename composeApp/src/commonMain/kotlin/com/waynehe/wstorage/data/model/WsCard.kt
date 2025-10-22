package com.waynehe.wstorage.data.model

data class WsCard(
    val id: String,
    val seriesId: String,
    val cardCode: String,
    val title: String,
    val rarity: Rarity,
    val description: String,
    val effect: String? = null,
    val color: String? = null,
    val level: Int? = null,
    val cost: Int? = null,
    val imageUrl: String? = null,
    val ownedCount: Int = 0,
    val wishlistCount: Int = 0
)
