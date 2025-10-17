package com.waynehe.wstorage.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class CardDataBundle(
    @SerialName("series")
    val series: List<WsSeries> = emptyList(),
    @SerialName("cards")
    val cards: List<WsCard> = emptyList()
)
