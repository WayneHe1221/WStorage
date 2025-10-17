package com.waynehe.wstorage.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class CardPage(
    @SerialName("items")
    val items: List<WsCard>,
    @SerialName("page")
    val page: Int,
    @SerialName("pageSize")
    val pageSize: Int,
    @SerialName("totalCount")
    val totalCount: Int,
    @SerialName("hasMore")
    val hasMore: Boolean
)
