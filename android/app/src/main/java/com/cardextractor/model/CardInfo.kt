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
 * on-device). Inputs are BOTH sides of the card (front + back). Single source of truth;
 * Pydantic and Kotlin types are generated from this file. Extraction hint: year, brand, set
 * and subset are most often printed at the bottom of the card front, and on the label if
 * graded. NOTE: when card_type is 'graded', the 'graded' object should be present (may
 * contain nulls if unreadable).
 */
@Serializable
data class CardInfo (
    val attributes: Attributes,

    /**
     * Autograph/signature details.
     */
    val autograph: Autograph? = null,

    /**
     * Card brand/maker (Topps, Panini, Upper Deck, Bowman, Fleer, ...), normalized. Often
     * printed at the bottom of the card and on the graded label.
     */
    val brand: String? = null,

    /**
     * The card's number WITHIN the set, as printed (e.g. '#250', 'RC-12'). NOT the
     * serial/print-run numbering like 5/30 — that goes in attributes.serial_number/serial_limit.
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
     * Embedded memorabilia details (patch/ball/floor/jersey/shoe pieces). There can be more
     * than one piece in a card.
     */
    val memorabilia: Memorabilia? = null,

    /**
     * Parallel/variation, e.g. 'Silver Prizm'.
     */
    val parallel: String? = null,

    /**
     * Confidence in [0,1] for individual fields, keyed by field name (dot-paths allowed, e.g.
     * 'autograph.ink_color').
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
     * Product/set name, normalized. Often printed at the bottom of the card and on the graded
     * label.
     */
    val set: String? = null,

    /**
     * Sport the card belongs to (football = American football).
     */
    val sport: Sport? = null,

    /**
     * Insert/subset name, if any. Often printed at the bottom of the card and on the graded
     * label.
     */
    val subset: String? = null,

    /**
     * Player's team/franchise name, if present.
     */
    val team: String? = null,

    /**
     * Card year or season, e.g. '2003' or '2003-04'. Often printed at the bottom of the card
     * and on the graded label.
     */
    val year: String? = null
)

/**
 * Card attribute flags and serial-numbering info.
 */
@Serializable
data class Attributes (
    /**
     * Rookie card (RC).
     */
    val rookie: Boolean? = null,

    /**
     * For a serial-numbered (limited) card such as '07/99', the total print run / population
     * (the 99).
     */
    @SerialName("serial_limit")
    val serialLimit: String? = null,

    /**
     * True when the copy's serial number equals the player's jersey number (e.g. 07/99 for a
     * player wearing #7) — such 'jersey-numbered' copies are rarer/more valuable. Null if
     * unknown.
     */
    @SerialName("serial_matches_jersey_number")
    val serialMatchesJerseyNumber: Boolean? = null,

    /**
     * For a serial-numbered (limited) card such as '07/99', this copy's own number (the 07).
     * Shows which copy this is out of the print run — NOT the card's number within the set.
     */
    @SerialName("serial_number")
    val serialNumber: String? = null
)

/**
 * Autograph/signature details.
 */
@Serializable
data class Autograph (
    /**
     * Color of the signature ink (e.g. 'black', 'blue', 'gold', 'silver'). Black is the
     * standard; any other color is rarer/more valuable.
     */
    @SerialName("ink_color")
    val inkColor: String? = null,

    /**
     * Does the card contain an autograph? Null if unknown.
     */
    val present: Boolean? = null
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
     * The descriptive information line(s) from the graded label (year/brand/set/player/card# as
     * the grader printed them).
     */
    val description: String? = null,

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
     * Full raw OCR of the label, for reference.
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
 * Embedded memorabilia in the card/slab. 'pieces' lists each embedded piece (can be more
 * than one).
 */
@Serializable
data class Memorabilia (
    /**
     * Each embedded piece, analyzed individually.
     */
    val pieces: List<MemorabiliaPiece>? = null,

    /**
     * Does the card contain memorabilia? Null if unknown.
     */
    val present: Boolean? = null
)

/**
 * One embedded memorabilia piece. A card can contain several.
 */
@Serializable
data class MemorabiliaPiece (
    /**
     * Distinct colors visible in the piece (e.g. ['wine','white','gold']).
     */
    val colors: List<String>? = null,

    /**
     * Does the piece contain part of the player's name (nameplate letters)? Null if unclear.
     */
    @SerialName("contains_player_name_part")
    val containsPlayerNamePart: Boolean? = null,

    /**
     * Does the piece contain part of the team logo? Null if unclear.
     */
    @SerialName("contains_team_logo_part")
    val containsTeamLogoPart: Boolean? = null,

    /**
     * Does the piece contain part of the team name lettering? Null if unclear.
     */
    @SerialName("contains_team_name_part")
    val containsTeamNamePart: Boolean? = null,

    /**
     * Is it an actual piece of fabric/material (true) vs a printed/manufactured facsimile
     * (false)? Null if unclear.
     */
    @SerialName("is_fabric")
    val isFabric: Boolean? = null,

    /**
     * Any letters/characters visible in the piece, as read (e.g. 'AME'). Null if none.
     */
    @SerialName("letters_visible")
    val lettersVisible: String? = null,

    /**
     * Kind of piece: patch (multi-color jersey patch), jersey (plain jersey swatch), ball,
     * floor, shoe, or other.
     */
    val type: PieceType? = null,

    /**
     * Number of unique colors in the piece (more colors usually = rarer patch).
     */
    @SerialName("unique_color_count")
    val uniqueColorCount: Long? = null
)

/**
 * Kind of embedded memorabilia piece.
 */
@Serializable
enum class PieceType(val value: String) {
    @SerialName("ball") Ball("ball"),
    @SerialName("floor") Floor("floor"),
    @SerialName("jersey") Jersey("jersey"),
    @SerialName("other") Other("other"),
    @SerialName("patch") Patch("patch"),
    @SerialName("shoe") Shoe("shoe");
}

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
     * Best guess for the number on the jersey in the card's picture, if visible (as printed,
     * e.g. '23').
     */
    @SerialName("jersey_number")
    val jerseyNumber: String? = null,

    /**
     * If the jersey number is uncertain (partially visible/occluded), all plausible candidates,
     * best first (e.g. ['8','3']). Null/empty when jersey_number is confident or not visible.
     */
    @SerialName("jersey_number_candidates")
    val jerseyNumberCandidates: List<String>? = null
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
     * References/hashes of the input image(s) — front and back.
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

@Serializable
enum class Sport(val value: String) {
    @SerialName("baseball") Baseball("baseball"),
    @SerialName("basketball") Basketball("basketball"),
    @SerialName("football") Football("football"),
    @SerialName("hockey") Hockey("hockey"),
    @SerialName("other") Other("other"),
    @SerialName("soccer") Soccer("soccer");
}
