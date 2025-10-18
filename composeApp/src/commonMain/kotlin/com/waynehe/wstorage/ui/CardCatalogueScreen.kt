package com.waynehe.wstorage.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
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
import com.russhwolf.settings.Settings
import com.waynehe.wstorage.data.model.InventoryEntry
import com.waynehe.wstorage.data.model.Rarity
import com.waynehe.wstorage.data.model.WsCard
import com.waynehe.wstorage.data.model.WsSeries
import com.waynehe.wstorage.data.repository.CardRepository
import com.waynehe.wstorage.data.repository.InMemoryCardRepository
import com.waynehe.wstorage.data.repository.InventoryRepository
import com.waynehe.wstorage.data.repository.SettingsInventoryRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

private const val DEFAULT_PAGE_SIZE = 50

@Composable
fun CardCatalogueScreen(
    modifier: Modifier = Modifier,
    repository: CardRepository? = null,
    inventoryRepository: InventoryRepository? = null,
    onCardSelected: (String) -> Unit = {}
) {
    val resolvedRepository = remember(repository) { repository ?: InMemoryCardRepository() }
    val resolvedInventoryRepository = remember(inventoryRepository) {
        inventoryRepository ?: SettingsInventoryRepository(Settings())
    }
    val presenter = rememberCardCataloguePresenter(resolvedRepository, resolvedInventoryRepository)
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

        SearchAndFilterPanel(
            searchText = uiState.searchText,
            onSearchTextChanged = presenter::onSearchTextChanged,
            selectedRarity = uiState.selectedRarity,
            onRaritySelected = presenter::onRaritySelected,
            availableColors = uiState.availableColors,
            selectedColors = uiState.selectedColors,
            onColorToggled = presenter::onColorFilterToggled
        )

        val errorMessage = uiState.errorMessage

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

            errorMessage != null -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = errorMessage,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.error
                    )
                }
            }

            else -> {
                CardCatalogueList(
                    cards = uiState.cards,
                    isLoading = uiState.isLoading,
                    onCardSelected = onCardSelected,
                    onIncrementOwned = presenter::onIncrementOwned,
                    onDecrementOwned = presenter::onDecrementOwned,
                    onIncrementWishlist = presenter::onIncrementWishlist,
                    onDecrementWishlist = presenter::onDecrementWishlist
                )
            }
        }
    }
}

@Composable
private fun rememberCardCataloguePresenter(
    repository: CardRepository,
    inventoryRepository: InventoryRepository
): CardCataloguePresenter {
    val presenter = remember(repository, inventoryRepository) {
        CardCataloguePresenter(repository, inventoryRepository)
    }
    DisposableEffect(presenter) {
        onDispose { presenter.dispose() }
    }
    return presenter
}

private class CardCataloguePresenter(
    private val repository: CardRepository,
    private val inventoryRepository: InventoryRepository,
    coroutineDispatcher: CoroutineDispatcher = Dispatchers.Default
) {
    private val scope = CoroutineScope(SupervisorJob() + coroutineDispatcher)
    private val _state = MutableStateFlow(CardCatalogueUiState())
    val state: StateFlow<CardCatalogueUiState> = _state.asStateFlow()

    private var allCards: List<WsCard> = emptyList()
    private var inventorySnapshot: Map<String, InventoryEntry> = emptyMap()

    init {
        refreshSeries()
        scope.launch {
            inventoryRepository.entries.collect { entries ->
                inventorySnapshot = entries
                refreshDisplayedCards()
            }
        }
    }

    fun onSeriesSelected(seriesId: String) {
        if (seriesId == _state.value.selectedSeriesId && allCards.isNotEmpty()) {
            return
        }
        loadCards(seriesId)
    }

    fun onSearchTextChanged(value: String) {
        updateStateAndRefresh { it.copy(searchText = value) }
    }

    fun onRaritySelected(rarity: Rarity?) {
        updateStateAndRefresh { it.copy(selectedRarity = rarity) }
    }

    fun onColorFilterToggled(color: String) {
        val normalized = color.uppercase()
        updateStateAndRefresh { state ->
            val updated = state.selectedColors.toMutableSet()
            if (!updated.add(normalized)) {
                updated.remove(normalized)
            }
            state.copy(selectedColors = updated)
        }
    }

    fun onIncrementOwned(cardId: String) {
        scope.launch { inventoryRepository.incrementOwned(cardId) }
    }

    fun onDecrementOwned(cardId: String) {
        scope.launch { inventoryRepository.decrementOwned(cardId) }
    }

    fun onIncrementWishlist(cardId: String) {
        scope.launch { inventoryRepository.incrementWishlist(cardId) }
    }

    fun onDecrementWishlist(cardId: String) {
        scope.launch { inventoryRepository.decrementWishlist(cardId) }
    }

    fun dispose() {
        scope.cancel()
    }

    private fun refreshSeries() {
        scope.launch {
            runCatching { repository.getAllSeries() }
                .onSuccess { series ->
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
                }
                .onFailure { error ->
                    allCards = emptyList()
                    _state.update {
                        it.copy(
                            series = emptyList(),
                            selectedSeriesId = null,
                            cards = emptyList(),
                            availableColors = emptySet(),
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
                    errorMessage = null,
                    cards = emptyList(),
                    availableColors = emptySet()
                )
            }
            allCards = emptyList()
            runCatching {
                repository.getCardsBySeries(seriesId, page = 0, pageSize = DEFAULT_PAGE_SIZE)
            }.onSuccess { page ->
                allCards = page.items
                _state.update {
                    it.copy(isLoading = false, errorMessage = null)
                }
                refreshDisplayedCards()
            }.onFailure { error ->
                allCards = emptyList()
                _state.update {
                    it.copy(
                        cards = emptyList(),
                        availableColors = emptySet(),
                        isLoading = false,
                        errorMessage = error.message ?: "讀取卡牌資料時發生錯誤"
                    )
                }
            }
        }
    }

    private fun refreshDisplayedCards() {
        val currentCards = allCards
        val availableColors = currentCards.mapNotNull { it.color?.uppercase() }.toSortedSet()
        val inventory = inventorySnapshot
        _state.update { current ->
            val sanitizedColors = current.selectedColors.filter { it in availableColors }.toSet()
            val adjustedState = current.copy(
                selectedColors = sanitizedColors,
                availableColors = availableColors
            )
            val filteredCards = applyFilters(currentCards, adjustedState)
            adjustedState.copy(cards = buildSummaries(filteredCards, inventory))
        }
    }

    private fun applyFilters(cards: List<WsCard>, state: CardCatalogueUiState): List<WsCard> {
        var filtered = cards
        val keyword = state.searchText.trim()
        if (keyword.isNotEmpty()) {
            val normalized = keyword.lowercase()
            filtered = filtered.filter { card ->
                card.title.lowercase().contains(normalized) ||
                    card.cardCode.lowercase().contains(normalized)
            }
        }
        state.selectedRarity?.let { rarity ->
            filtered = filtered.filter { it.rarity == rarity }
        }
        if (state.selectedColors.isNotEmpty()) {
            val selected = state.selectedColors
            filtered = filtered.filter { card ->
                card.color?.uppercase()?.let(selected::contains) == true
            }
        }
        return filtered
    }

    private fun buildSummaries(
        cards: List<WsCard>,
        inventory: Map<String, InventoryEntry>
    ): List<CardSummary> {
        return cards.map { card ->
            val entry = inventory[card.id]
            val owned = entry?.ownedCount ?: card.ownedCount
            val wishlist = entry?.wishlistCount ?: card.wishlistCount
            CardSummary(
                id = card.id,
                title = card.title,
                cardCode = card.cardCode,
                rarityLabel = card.rarity.name.replace('_', ' '),
                imageUrl = card.imageUrl,
                ownedCount = owned,
                wishlistCount = wishlist
            )
        }
    }

    private fun updateStateAndRefresh(transform: (CardCatalogueUiState) -> CardCatalogueUiState) {
        _state.update(transform)
        refreshDisplayedCards()
    }
}

private data class CardCatalogueUiState(
    val isLoading: Boolean = false,
    val series: List<WsSeries> = emptyList(),
    val selectedSeriesId: String? = null,
    val searchText: String = "",
    val selectedRarity: Rarity? = null,
    val selectedColors: Set<String> = emptySet(),
    val availableColors: Set<String> = emptySet(),
    val cards: List<CardSummary> = emptyList(),
    val errorMessage: String? = null
)

data class CardSummary(
    val id: String,
    val title: String,
    val cardCode: String,
    val rarityLabel: String,
    val imageUrl: String?,
    val ownedCount: Int,
    val wishlistCount: Int
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
    onCardSelected: (String) -> Unit,
    onIncrementOwned: (String) -> Unit,
    onDecrementOwned: (String) -> Unit,
    onIncrementWishlist: (String) -> Unit,
    onDecrementWishlist: (String) -> Unit
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
                CardCatalogueRow(
                    card = card,
                    onCardSelected = onCardSelected,
                    onIncrementOwned = { onIncrementOwned(card.id) },
                    onDecrementOwned = { onDecrementOwned(card.id) },
                    onIncrementWishlist = { onIncrementWishlist(card.id) },
                    onDecrementWishlist = { onDecrementWishlist(card.id) }
                )
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
private fun CardCatalogueRow(
    card: CardSummary,
    onCardSelected: (String) -> Unit,
    onIncrementOwned: () -> Unit,
    onDecrementOwned: () -> Unit,
    onIncrementWishlist: () -> Unit,
    onDecrementWishlist: () -> Unit
) {
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
                InventoryAdjustRow(
                    label = "庫存",
                    count = card.ownedCount,
                    onIncrement = onIncrementOwned,
                    onDecrement = onDecrementOwned
                )
                Spacer(modifier = Modifier.height(4.dp))
                InventoryAdjustRow(
                    label = "願望清單",
                    count = card.wishlistCount,
                    onIncrement = onIncrementWishlist,
                    onDecrement = onDecrementWishlist
                )
            }
        }
    }
}

@Composable
private fun InventoryAdjustRow(
    label: String,
    count: Int,
    onIncrement: () -> Unit,
    onDecrement: () -> Unit
) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(
            text = "$label：$count",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.width(8.dp))
        InventoryActionButton(text = "-", onClick = onDecrement)
        Spacer(modifier = Modifier.width(4.dp))
        InventoryActionButton(text = "+", onClick = onIncrement)
    }
}

@Composable
private fun InventoryActionButton(text: String, onClick: () -> Unit) {
    OutlinedButton(
        onClick = onClick,
        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
    ) {
        Text(text = text, style = MaterialTheme.typography.labelLarge)
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

@Composable
private fun SearchAndFilterPanel(
    searchText: String,
    onSearchTextChanged: (String) -> Unit,
    selectedRarity: Rarity?,
    onRaritySelected: (Rarity?) -> Unit,
    availableColors: Set<String>,
    selectedColors: Set<String>,
    onColorToggled: (String) -> Unit
) {
    Column(modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp)) {
        OutlinedTextField(
            value = searchText,
            onValueChange = onSearchTextChanged,
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            label = { Text("搜尋卡牌") }
        )
        Spacer(modifier = Modifier.height(12.dp))
        Text(
            text = "稀有度篩選",
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(8.dp))
        Row(
            modifier = Modifier.horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            FilterChip(
                selected = selectedRarity == null,
                onClick = { onRaritySelected(null) },
                label = { Text("全部") }
            )
            Rarity.entries.forEach { rarity ->
                val display = rarity.name.replace('_', ' ')
                FilterChip(
                    selected = selectedRarity == rarity,
                    onClick = { onRaritySelected(rarity) },
                    label = { Text(display) }
                )
            }
        }
        Spacer(modifier = Modifier.height(12.dp))
        Text(
            text = "顏色篩選",
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(8.dp))
        if (availableColors.isEmpty()) {
            Text(
                text = "此系列尚無顏色資料",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        } else {
            Row(
                modifier = Modifier.horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                availableColors.forEach { color ->
                    val isSelected = selectedColors.contains(color)
                    FilterChip(
                        selected = isSelected,
                        onClick = { onColorToggled(color) },
                        label = { Text(color) }
                    )
                }
            }
        }
    }
}
