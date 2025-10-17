package com.waynehe.wstorage

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import org.jetbrains.compose.ui.tooling.preview.Preview
import com.waynehe.wstorage.data.repository.InMemoryCardRepository

@Composable
@Preview
fun App() {
    MaterialTheme {
        Column(
            modifier = Modifier
                .background(MaterialTheme.colorScheme.background)
                .fillMaxSize()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            val cardRepository = remember { InMemoryCardRepository() }
            val previewSeries by remember(cardRepository) {
                mutableStateOf(cardRepository.getAllSeries())
            }

            Text(
                text = "WStorage",
                style = MaterialTheme.typography.headlineMedium
            )
            Text(
                text = "Series in repository: ${previewSeries.size}",
                style = MaterialTheme.typography.bodyMedium
            )
            previewSeries.forEach { series ->
                Text(
                    text = "• ${series.name} (${series.setCode})",
                    style = MaterialTheme.typography.bodySmall
                )
            }
        }
    }
}