package com.cardextractor.app.vision

import android.content.Context
import android.net.Uri
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import kotlinx.coroutines.tasks.await

/** ML Kit Text Recognition v2 (on-device, Latin model) — roadmap P3-3. */
class OcrEngine {

    private val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)

    /** Returns recognized text lines joined with newlines (parser input format). */
    suspend fun recognize(context: Context, uri: Uri): String {
        val image = InputImage.fromFilePath(context, uri)
        val result = recognizer.process(image).await()
        return result.textBlocks
            .flatMap { it.lines }
            .joinToString("\n") { it.text }
    }
}
