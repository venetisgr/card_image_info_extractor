package com.cardextractor.app.extract

import android.content.Context
import android.net.Uri
import com.cardextractor.app.net.BackendApi
import com.cardextractor.app.vision.BarcodeEngine
import com.cardextractor.app.vision.OcrEngine
import com.cardextractor.model.CardInfo
import com.cardextractor.parser.OcrCardParser
import com.cardextractor.parser.OcrInput
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody

/** Which engine handles a scan (roadmap P3-8 mode toggle). */
enum class ExtractorMode { ON_DEVICE, CLOUD }

interface Extractor {
    suspend fun extract(context: Context, front: Uri, back: Uri?): CardInfo
}

/**
 * Engine B baseline: ML Kit OCR + barcodes -> rules parser (:core).
 * Fully offline; visual-only fields stay null until Phase 4 models land.
 */
class OnDeviceExtractor(
    private val ocr: OcrEngine = OcrEngine(),
    private val barcodes: BarcodeEngine = BarcodeEngine(),
) : Extractor {

    override suspend fun extract(context: Context, front: Uri, back: Uri?): CardInfo {
        val frontText = ocr.recognize(context, front)
        val backText = back?.let { ocr.recognize(context, it) }
        val codes = buildList {
            addAll(barcodes.scan(context, front))
            back?.let { addAll(barcodes.scan(context, it)) }
        }
        return OcrCardParser.parse(
            OcrInput(
                frontText = frontText,
                backText = backText,
                barcodes = codes,
                sourceImages = listOfNotNull(front.toString(), back?.toString()),
            )
        )
    }
}

/**
 * Engine A via our backend: full Claude extraction (+ PSA verification when
 * the server has a token). Used for cloud mode and low-confidence fallback.
 */
class CloudExtractor(
    private val api: BackendApi,
    private val json: Json,
) : Extractor {

    override suspend fun extract(context: Context, front: Uri, back: Uri?): CardInfo {
        val response = api.extract(
            front = uriPart(context, "front", front),
            back = back?.let { uriPart(context, "back", it) },
        )
        return json.decodeFromString(CardInfo.serializer(), response.string())
    }

    private fun uriPart(context: Context, name: String, uri: Uri): MultipartBody.Part {
        val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
            ?: error("cannot read $name image at $uri")
        return MultipartBody.Part.createFormData(
            name,
            "$name.jpg",
            bytes.toRequestBody("image/jpeg".toMediaType()),
        )
    }
}
