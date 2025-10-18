package com.waynehe.wstorage.data.model

enum class Rarity(val code: String) {
    COMMON("C"),
    UNCOMMON("U"),
    RARE("R"),
    SUPER_RARE("SR"),
    SPECIAL("SP");

    companion object {
        fun fromCode(value: String): Rarity? = entries.firstOrNull { it.code.equals(value, ignoreCase = true) }
    }
}
