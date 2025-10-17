package com.waynehe.wstorage.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class Rarity {
    @SerialName("C")
    COMMON,

    @SerialName("U")
    UNCOMMON,

    @SerialName("R")
    RARE,

    @SerialName("SR")
    SUPER_RARE,

    @SerialName("SP")
    SPECIAL
}
