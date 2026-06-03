// To parse the JSON, install kotlin's serialization plugin and do:
//
// val json     = Json { allowStructuredMapKeys = true }
// val cardInfo = json.parse(CardInfo.serializer(), jsonString)

package com.cardextractor.model

import kotlinx.serialization.*
import kotlinx.serialization.json.*
import kotlinx.serialization.descriptors.*
import kotlinx.serialization.encoding.*

/**
 * Canonical structured record for a sports card extracted by either engine (Claude API or
 * on-device). Single source of truth; Pydantic and Kotlin types are generated from this
 * file. NOTE: when card_type is 'graded', the 'graded' object should be present (may
 * contain nulls if unreadable).
 */
@Serializable
data class CardInfo (
    val attributes: Attributes,

    /**
     * Card number exactly as printed, e.g. 'RC-12' or '#250'.
     */
    @SerialName("card_number")
    val cardNumber: String? = null,

    /**
     * Whether the card is professionally graded/slabbed or raw (loose).
     */
    @SerialName("card_type")
    val cardType: CardType,

    /**
     * Grading details; present when card_type is 'graded'.
     */
    val graded: GradedInfo? = null,

    /**
     * ISO language code if detectable.
     */
    val language: String? = null,

    /**
     * Card maker (Topps, Panini, Upper Deck, Bowman, Fleer, ...), normalized.
     */
    val manufacturer: String? = null,

    /**
     * Parallel/variation, e.g. 'Silver Prizm'.
     */
    val parallel: String? = null,

    /**
     * Confidence in [0,1] for individual fields, keyed by field name.
     */
    @SerialName("per_field_confidence")
    val perFieldConfidence: Map<String, Double>,

    /**
     * Visual details of the player's picture printed on the card.
     */
    val photo: Photo? = null,

    /**
     * Subject/athlete name as printed.
     */
    @SerialName("player_name")
    val playerName: String? = null,

    val provenance: Provenance,

    /**
     * Raw engine output (OCR text or model JSON) for debugging.
     */
    @SerialName("raw_output")
    val rawOutput: JsonObject? = null,

    /**
     * Embedded memorabilia/relic details; present for relic ('jersey piece') cards.
     */
    val relic: Relic? = null,

    /**
     * Product/set name, normalized.
     */
    val set: String? = null,

    /**
     * Sport the card belongs to.
     */
    val sport: Sport? = null,

    /**
     * Insert/subset name, if any.
     */
    val subset: String? = null,

    /**
     * Team/franchise, if present.
     */
    val team: String? = null,

    /**
     * Card year or season, e.g. '2003' or '2003-04'.
     */
    val year: String? = null
)

/**
 * Card attribute flags and serial-numbering info.
 */
@Serializable
data class Attributes (
    /**
     * Contains an autograph.
     */
    val autograph: Boolean? = null,

    /**
     * Contains a relic/memorabilia/patch.
     */
    val relic: Boolean? = null,

    /**
     * Rookie card (RC).
     */
    val rookie: Boolean? = null,

    /**
     * For a serial-numbered (limited) card such as '5/30', the total print run/population (the
     * 30).
     */
    @SerialName("serial_limit")
    val serialLimit: String? = null,

    /**
     * For a serial-numbered (limited) card such as '5/30', this card's own number (the 5).
     */
    @SerialName("serial_number")
    val serialNumber: String? = null
)

/**
 * Whether the card is professionally graded/slabbed or raw (loose).
 */
@Serializable
enum class CardType(val value: String) {
    @SerialName("graded") Graded("graded"),
    @SerialName("raw") Raw("raw");
}

/**
 * Details read from a graded slab label and/or verified via a cert API.
 */
@Serializable
data class GradedInfo (
    /**
     * Certification/serial number on the slab.
     */
    @SerialName("cert_number")
    val certNumber: String? = null,

    /**
     * Numeric grade, e.g. 10 or 9.5.
     */
    val grade: Double? = null,

    /**
     * Grade label as printed, e.g. 'GEM-MT 10'.
     */
    @SerialName("grade_label")
    val gradeLabel: String? = null,

    /**
     * Grading company. BGS = Beckett Grading Services.
     */
    @SerialName("grading_company")
    val gradingCompany: GradingCompany? = null,

    /**
     * Full OCR of the label, for reference.
     */
    @SerialName("label_text")
    val labelText: String? = null,

    val subgrades: Subgrades? = null
)

@Serializable
enum class GradingCompany(val value: String) {
    @SerialName("BGS") Bgs("BGS"),
    @SerialName("CGC") Cgc("CGC"),
    @SerialName("other") Other("other"),
    @SerialName("PSA") PSA("PSA"),
    @SerialName("SGC") Sgc("SGC"),
    @SerialName("TAG") Tag("TAG");
}

/**
 * Per-aspect subgrades (e.g. BGS).
 */
@Serializable
data class Subgrades (
    val centering: Double? = null,
    val corners: Double? = null,
    val edges: Double? = null,
    val surface: Double? = null
)

/**
 * Visual details of the player's picture printed on the card.
 */
@Serializable
data class Photo (
    /**
     * Colors of the jersey the player is wearing in the card's picture, if visible (e.g.
     * ['red','black','white']).
     */
    @SerialName("jersey_colors")
    val jerseyColors: List<String>? = null,

    /**
     * Number shown on the jersey in the card's picture, if visible (as printed, e.g. '23').
     */
    @SerialName("jersey_number")
    val jerseyNumber: String? = null
)

/**
 * Where/how this record was produced.
 */
@Serializable
data class Provenance (
    /**
     * Which engine produced this.
     */
    val engine: Engine,

    /**
     * Model id (e.g. 'claude-opus-4-8') or app build.
     */
    @SerialName("model_version")
    val modelVersion: String,

    /**
     * References/hashes of the input image(s).
     */
    @SerialName("source_images")
    val sourceImages: List<String>? = null,

    /**
     * ISO-8601 timestamp.
     */
    val timestamp: String
)

/**
 * Which engine produced this.
 */
@Serializable
enum class Engine(val value: String) {
    @SerialName("claude") Claude("claude"),
    @SerialName("on_device") OnDevice("on_device");
}

/**
 * Details of an embedded memorabilia/relic piece (e.g. a real jersey swatch) in the
 * card/slab.
 */
@Serializable
data class Relic (
    /**
     * Colors of the embedded real-life jersey/memorabilia piece, if present (e.g.
     * ['blue','white']).
     */
    @SerialName("swatch_colors")
    val swatchColors: List<String>? = null
)

@Serializable
enum class Sport(val value: String) {
    @SerialName("baseball") Baseball("baseball"),
    @SerialName("basketball") Basketball("basketball"),
    @SerialName("football") Football("football"),
    @SerialName("hockey") Hockey("hockey"),
    @SerialName("other") Other("other"),
    @SerialName("soccer") Soccer("soccer");
}
