package com.cardextractor.app

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.cardextractor.app.db.AppDb
import com.cardextractor.app.db.ScanEntity
import com.cardextractor.app.extract.CloudExtractor
import com.cardextractor.app.extract.ExtractorMode
import com.cardextractor.app.extract.OnDeviceExtractor
import com.cardextractor.app.net.BackendApi
import com.cardextractor.model.CardInfo
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json

data class ScanUiState(
    val frontUri: Uri? = null,
    val backUri: Uri? = null,
    val mode: ExtractorMode = ExtractorMode.ON_DEVICE,
    val busy: Boolean = false,
    val error: String? = null,
    val result: CardInfo? = null,
    val resultJson: String? = null,
)

class MainViewModel(app: Application) : AndroidViewModel(app) {

    private val json = Json {
        ignoreUnknownKeys = true
        prettyPrint = true
        allowStructuredMapKeys = true
    }
    private val onDevice = OnDeviceExtractor()
    private val cloud = CloudExtractor(BackendApi.create(), json)
    private val db = AppDb.get(app)

    private val _state = MutableStateFlow(ScanUiState())
    val state: StateFlow<ScanUiState> = _state.asStateFlow()

    val history = db.scans().all()

    fun setFront(uri: Uri?) = _state.value.let { _state.value = it.copy(frontUri = uri, result = null) }
    fun setBack(uri: Uri?) = _state.value.let { _state.value = it.copy(backUri = uri, result = null) }
    fun setMode(mode: ExtractorMode) { _state.value = _state.value.copy(mode = mode) }

    fun extract() {
        val current = _state.value
        val front = current.frontUri ?: run {
            _state.value = current.copy(error = "Add a front photo first")
            return
        }
        _state.value = current.copy(busy = true, error = null, result = null)
        viewModelScope.launch {
            try {
                val extractor = if (current.mode == ExtractorMode.CLOUD) cloud else onDevice
                val card = extractor.extract(getApplication(), front, current.backUri)
                val encoded = json.encodeToString(CardInfo.serializer(), card)
                db.scans().insert(
                    ScanEntity(
                        createdAt = System.currentTimeMillis(),
                        engine = card.provenance.engine.value,
                        cardType = card.cardType.value,
                        playerName = card.playerName,
                        summary = listOfNotNull(
                            card.playerName,
                            card.year,
                            card.set ?: card.brand,
                            card.graded?.gradeLabel,
                        ).joinToString(" · ").ifEmpty { "unidentified card" },
                        cardJson = encoded,
                    )
                )
                _state.value = _state.value.copy(busy = false, result = card, resultJson = encoded)
            } catch (e: Exception) {
                _state.value = _state.value.copy(busy = false, error = e.message ?: "extraction failed")
            }
        }
    }
}
