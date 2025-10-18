package com.waynehe.wstorage.data.model

data class CardPage(
    val items: List<WsCard>,
    val page: Int,
    val pageSize: Int,
    val totalCount: Int,
    val hasMore: Boolean
)
