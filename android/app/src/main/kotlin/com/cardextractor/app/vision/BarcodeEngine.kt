package com.cardextractor.app.vision

import android.content.Context
import android.net.Uri
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.common.InputImage
import kotlinx.coroutines.tasks.await

/** ML Kit barcode scanning — slab labels carry the cert number (roadmap P3-4). */
class BarcodeEngine {

    private val scanner = BarcodeScanning.getClient()

    suspend fun scan(context: Context, uri: Uri): List<String> {
        val image = InputImage.fromFilePath(context, uri)
        return scanner.process(image).await().mapNotNull { it.rawValue }
    }
}
