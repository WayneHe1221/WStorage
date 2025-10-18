package com.waynehe.wstorage.data.model

data class CardDataBundle(
    val series: List<WsSeries> = emptyList(),
    val cards: List<WsCard> = emptyList()
)
