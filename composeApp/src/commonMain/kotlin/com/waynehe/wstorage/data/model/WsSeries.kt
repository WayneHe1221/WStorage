package com.waynehe.wstorage.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class WsSeries(
    @SerialName("id")
    val id: String,
    @SerialName("name")
    val name: String,
    @SerialName("setCode")
    val setCode: String,
    @SerialName("releaseYear")
    val releaseYear: Int
)
