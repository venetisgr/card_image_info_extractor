package com.cardextractor.parser

/** Raw signals gathered on-device before parsing. */
data class OcrInput(
    /** OCR text of the front photo (ML Kit blocks joined with newlines). */
    val frontText: String? = null,
    /** OCR text of the back photo, when captured. */
    val backText: String? = null,
    /** Raw payloads of any barcodes/QR codes found (slab labels carry the cert). */
    val barcodes: List<String> = emptyList(),
    /** References for provenance (e.g. content-URI strings or hashes). */
    val sourceImages: List<String> = emptyList(),
)
