package com.waynehe.wstorage.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class WsCard(
    @SerialName("id")
    val id: String,
    @SerialName("seriesId")
    val seriesId: String,
    @SerialName("cardCode")
    val cardCode: String,
    @SerialName("title")
    val title: String,
    @SerialName("rarity")
    val rarity: Rarity,
    @SerialName("description")
    val description: String,
    @SerialName("color")
    val color: String? = null,
    @SerialName("level")
    val level: Int? = null,
    @SerialName("cost")
    val cost: Int? = null,
    @SerialName("imageUrl")
    val imageUrl: String? = null
)
