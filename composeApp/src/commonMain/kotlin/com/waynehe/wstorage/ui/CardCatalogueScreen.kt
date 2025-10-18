package com.waynehe.wstorage.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ScrollableTabRow
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.waynehe.wstorage.data.model.WsSeries
import com.waynehe.wstorage.data.repository.CardRepository
import com.waynehe.wstorage.data.repository.InMemoryCardRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

private const val DEFAULT_PAGE_SIZE = 50

@Composable
fun CardCatalogueScreen(
    modifier: Modifier = Modifier,
    repository: CardRepository? = null,
    onCardSelected: (String) -> Unit = {}
) {
    val resolvedRepository = remember(repository) { repository ?: InMemoryCardRepository() }
    val presenter = rememberCardCataloguePresenter(resolvedRepository)
    val uiState by presenter.state.collectAsState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(top = 16.dp)
    ) {
        Text(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            text = "卡牌一覽",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold
        )

        CatalogueTabs(
            series = uiState.series,
            selectedSeriesId = uiState.selectedSeriesId,
            onSeriesSelected = presenter::onSeriesSelected
        )

        when {
            uiState.isLoading && uiState.cards.isEmpty() -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            }

            uiState.errorMessage != null -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = uiState.errorMessage,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.error
                    )
                }
            }

            else -> {
                CardCatalogueList(
                    cards = uiState.cards,
                    isLoading = uiState.isLoading,
                    onCardSelected = onCardSelected
                )
            }
        }
    }
}

@Composable
private fun rememberCardCataloguePresenter(repository: CardRepository): CardCataloguePresenter {
    val presenter = remember(repository) { CardCataloguePresenter(repository) }
    DisposableEffect(presenter) {
        onDispose { presenter.dispose() }
    }
    return presenter
}

private class CardCataloguePresenter(
    private val repository: CardRepository,
    coroutineDispatcher: CoroutineDispatcher = Dispatchers.Default
) {
    private val scope = CoroutineScope(SupervisorJob() + coroutineDispatcher)
    private val _state = MutableStateFlow(CardCatalogueUiState())
    val state: StateFlow<CardCatalogueUiState> = _state.asStateFlow()

    private val inventoryByCardId = mapOf(
        "sao-10th-001" to 3,
        "sao-10th-002" to 1,
        "holo-vol2-001" to 2,
        "ba-001" to 5
    )

    init {
        refreshSeries()
    }

    fun onSeriesSelected(seriesId: String) {
        if (seriesId == _state.value.selectedSeriesId && _state.value.cards.isNotEmpty()) {
            return
        }
        loadCards(seriesId)
    }

    fun dispose() {
        scope.cancel()
    }

    private fun refreshSeries() {
        scope.launch {
            runCatching {
                repository.getAllSeries()
            }.onSuccess { series ->
                val selectedId = _state.value.selectedSeriesId ?: series.firstOrNull()?.id
                _state.update {
                    it.copy(
                        series = series,
                        selectedSeriesId = selectedId,
                        isLoading = selectedId != null,
                        errorMessage = null
                    )
                }
                if (selectedId != null) {
                    loadCards(selectedId)
                }
            }.onFailure { error ->
                _state.update {
                    it.copy(
                        series = emptyList(),
                        selectedSeriesId = null,
                        cards = emptyList(),
                        isLoading = false,
                        errorMessage = error.message ?: "無法載入資料"
                    )
                }
            }
        }
    }

    private fun loadCards(seriesId: String) {
        scope.launch {
            _state.update {
                it.copy(
                    selectedSeriesId = seriesId,
                    isLoading = true,
                    errorMessage = null
                )
            }
            runCatching {
                repository.getCardsBySeries(seriesId, page = 0, pageSize = DEFAULT_PAGE_SIZE)
            }.onSuccess { page ->
                val cards = page.items.map { card ->
                    CardSummary(
                        id = card.id,
                        title = card.title,
                        cardCode = card.cardCode,
                        rarityLabel = card.rarity.name.replace('_', ' '),
                        imageUrl = card.imageUrl,
                        stockCount = inventoryByCardId[card.id]
                    )
                }
                _state.update {
                    it.copy(
                        cards = cards,
                        isLoading = false,
                        errorMessage = null
                    )
                }
            }.onFailure { error ->
                _state.update {
                    it.copy(
                        cards = emptyList(),
                        isLoading = false,
                        errorMessage = error.message ?: "讀取卡牌資料時發生錯誤"
                    )
                }
            }
        }
    }
}

private data class CardCatalogueUiState(
    val isLoading: Boolean = false,
    val series: List<WsSeries> = emptyList(),
    val selectedSeriesId: String? = null,
    val cards: List<CardSummary> = emptyList(),
    val errorMessage: String? = null
)

data class CardSummary(
    val id: String,
    val title: String,
    val cardCode: String,
    val rarityLabel: String,
    val imageUrl: String?,
    val stockCount: Int?
)

@Composable
private fun CatalogueTabs(
    series: List<WsSeries>,
    selectedSeriesId: String?,
    onSeriesSelected: (String) -> Unit
) {
    if (series.isEmpty()) {
        return
    }
    val selectedIndex = series.indexOfFirst { it.id == selectedSeriesId }.let { index ->
        if (index >= 0) index else 0
    }

    ScrollableTabRow(
        selectedTabIndex = selectedIndex,
        edgePadding = 16.dp
    ) {
        series.forEachIndexed { index, item ->
            Tab(
                selected = index == selectedIndex,
                onClick = { onSeriesSelected(item.id) },
                text = {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(text = item.name, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text(
                            text = item.setCode,
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            )
        }
    }
}

@Composable
private fun CardCatalogueList(
    cards: List<CardSummary>,
    isLoading: Boolean,
    onCardSelected: (String) -> Unit
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(vertical = 8.dp)
    ) {
        if (cards.isEmpty() && !isLoading) {
            item {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(32.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "目前沒有卡牌資料",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        } else {
            items(cards) { card ->
                CardCatalogueRow(card = card, onCardSelected = onCardSelected)
            }
        }
        if (isLoading) {
            item {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(24.dp),
                    horizontalArrangement = Arrangement.Center
                ) {
                    CircularProgressIndicator(modifier = Modifier.size(32.dp))
                }
            }
        }
    }
}

@Composable
private fun CardCatalogueRow(card: CardSummary, onCardSelected: (String) -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
            .clickable { onCardSelected(card.id) },
        shape = MaterialTheme.shapes.medium
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.spacedBy(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            CardThumbnail(card)
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = card.title,
                    style = MaterialTheme.typography.titleMedium,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = card.cardCode,
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "稀有度：${card.rarityLabel}",
                    style = MaterialTheme.typography.bodySmall
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "庫存：${card.stockCount?.toString() ?: "--"}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
private fun CardThumbnail(card: CardSummary) {
    Box(
        modifier = Modifier
            .size(64.dp)
            .clip(MaterialTheme.shapes.small)
            .background(MaterialTheme.colorScheme.surfaceVariant),
        contentAlignment = Alignment.Center
    ) {
        val label = card.imageUrl?.takeIf { it.isNotBlank() }
            ?: card.title.firstOrNull()?.uppercaseChar()?.toString()
        Text(
            text = label ?: "?",
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}
