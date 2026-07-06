package com.cardextractor.parser

import com.cardextractor.model.Attributes
import com.cardextractor.model.Autograph
import com.cardextractor.model.CardInfo
import com.cardextractor.model.CardType
import com.cardextractor.model.Engine
import com.cardextractor.model.GradedInfo
import com.cardextractor.model.GradingCompany
import com.cardextractor.model.Memorabilia
import com.cardextractor.model.Provenance
import com.cardextractor.model.Subgrades
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive

/**
 * Rules-based OCR-text -> CardInfo parser (Engine B baseline, roadmap P3-5).
 *
 * Works purely on text: what OCR + barcodes can see. Visual-only fields
 * (jersey colors/numbers in the photo, memorabilia piece analysis) stay null
 * here — they arrive with the Phase 4 vision models or the cloud engine.
 */
object OcrCardParser {

    const val VERSION: String = "android-parser-0.1.0"

    // Longest grade words first so alternation prefers compounds (EX-MT over EX).
    private const val GRADE_VOCAB =
        "GEM\\s?-?\\s?(?:MT|MINT)|PRISTINE|NM\\s?-?\\s?MT|EX\\s?-?\\s?MT|VG\\s?-?\\s?EX|" +
            "MINT|NM|EX|VG|GOOD|FR|PR|AUTHENTIC"
    private const val GRADE_NUM = "10|[1-9](?:\\.5)?"

    private val gradeWordNum = Regex("($GRADE_VOCAB)\\s+($GRADE_NUM)\\b")
    private val gradeNumWord = Regex("\\b($GRADE_NUM)\\s+($GRADE_VOCAB)")
    private val certRegex = Regex("\\b\\d{7,10}\\b")
    private val serialRegex = Regex("\\b(\\d{1,4})\\s*/\\s*(\\d{1,4})\\b")
    private val yearRegex = Regex("\\b(?:19|20)\\d{2}(?:-\\d{2})?\\b")
    private val autographGradeRegex = Regex("\\b(10|[1-9](?:\\.5)?)\\s+AUTOGRAPH\\b")
    private val hashNumberRegex = Regex("#\\s?([A-Z0-9]{1,6}(?:-[A-Z0-9]{1,6})?)")
    private val cardNoRegex = Regex("CARD\\s+NO\\.?\\s*([A-Z0-9-]{1,8})")
    private val prefixedNumberRegex = Regex("\\b([A-Z]{2,4}-[A-Z0-9]{1,4})\\b")
    private val gradeCompoundWords = setOf("EX-MT", "NM-MT", "VG-EX", "GEM-MT", "GEM-MINT")
    private val subgradeNames = listOf("CENTERING", "CORNERS", "EDGES", "SURFACE")
    private val memorabiliaTokens = Regex(
        "JERSEY|PATCH|RELIC|GAME[- ]USED|GAME[- ]WORN|EVENT[- ]WORN|FLOOR PIECE|BALL PIECE"
    )
    private val autographTokens = Regex("AUTOGRAPH|\\bAUTO\\b|SIGNED BY")
    private val rookieTokens = Regex("\\bROOKIE\\b|\\bRC\\b")
    private val nameToken = Regex("^[A-Za-z.'-]{2,15}$")

    fun parse(input: OcrInput, timestamp: String = nowIso()): CardInfo {
        val front = input.frontText?.trim().orEmpty()
        val back = input.backText?.trim().orEmpty()
        val all = listOf(front, back).filter { it.isNotEmpty() }.joinToString("\n")
        val upper = all.uppercase()
        val confidence = mutableMapOf<String, Double>()

        // --- graded vs raw: a grading-company token on either face decides ---
        val company = Reference.gradingCompanies.entries
            .firstOrNull { Regex("\\b${it.key}\\b").containsMatchIn(upper) }?.value
        val isGraded = company != null
        confidence["card_type"] = if (isGraded) 0.9 else 0.7

        // The face carrying the company token is treated as the label face.
        val labelFace = when {
            !isGraded -> ""
            front.uppercase().containsCompany() -> front
            back.uppercase().containsCompany() -> back
            else -> front
        }

        val graded = if (isGraded) buildGraded(company!!, labelFace, all, input, confidence) else null

        // --- serial numbering (often stamped on the back) ---
        val serial = findSerial(all)
        serial?.let {
            confidence["attributes.serial_number"] = it.third
            confidence["attributes.serial_limit"] = it.third
        }

        // --- year / brand / set from the bundled reference subset ---
        val year = yearRegex.find(all)?.value
        year?.let { confidence["year"] = if (isGraded) 0.8 else 0.6 }

        val set = Reference.sets.entries.firstOrNull { upper.contains(it.key) }?.value
        // A recognized set names the brand more reliably than a token scan:
        // card backs cite the parent company ("(c) 2007 Donruss Playoff L.P."),
        // which would otherwise shadow the actual brand line.
        val brand = set?.let { Reference.setToBrand[it] }
            ?: Reference.brands.entries.firstOrNull { upper.contains(it.key) }?.value
        set?.let { confidence["set"] = 0.75 }
        brand?.let { confidence["brand"] = 0.75 }

        val cardNumber = findCardNumber(upper)
        cardNumber?.let { confidence["card_number"] = 0.7 }

        val sport = Reference.sportTokens.entries
            .firstOrNull { Regex("\\b${it.key}\\b").containsMatchIn(upper) }?.value
        sport?.let { confidence["sport"] = 0.7 }

        val playerName = findPlayerName(all)
        playerName?.let { confidence["player_name"] = 0.6 }

        val team = findTeam(all)
        team?.let { confidence["team"] = 0.6 }

        val hasAutograph = autographTokens.containsMatchIn(upper)
        if (hasAutograph) confidence["autograph.present"] = 0.8
        val hasMemorabilia = memorabiliaTokens.containsMatchIn(upper)
        if (hasMemorabilia) confidence["memorabilia.present"] = 0.7

        val rookie = rookieTokens.containsMatchIn(upper)
        if (rookie) confidence["attributes.rookie"] = 0.85

        return CardInfo(
            cardType = if (isGraded) CardType.Graded else CardType.Raw,
            sport = sport,
            playerName = playerName,
            year = year,
            brand = brand,
            set = set,
            subset = null,
            parallel = null,
            cardNumber = cardNumber,
            team = team,
            language = null,
            attributes = Attributes(
                rookie = rookie,
                serialNumber = serial?.first,
                serialLimit = serial?.second,
                serialMatchesJerseyNumber = null,
            ),
            photo = null,
            autograph = Autograph(present = if (hasAutograph) true else null, inkColor = null),
            memorabilia = Memorabilia(
                present = if (hasMemorabilia) true else null,
                pieces = emptyList(),
            ),
            graded = graded,
            perFieldConfidence = confidence,
            provenance = Provenance(
                engine = Engine.OnDevice,
                modelVersion = VERSION,
                timestamp = timestamp,
                sourceImages = input.sourceImages,
            ),
            rawOutput = JsonObject(
                buildMap {
                    if (front.isNotEmpty()) put("ocr_front", JsonPrimitive(front))
                    if (back.isNotEmpty()) put("ocr_back", JsonPrimitive(back))
                    if (input.barcodes.isNotEmpty()) {
                        put("barcodes", JsonPrimitive(input.barcodes.joinToString("|")))
                    }
                }
            ),
        )
    }

    // -- graded label ------------------------------------------------------

    private fun buildGraded(
        company: GradingCompany,
        labelFace: String,
        all: String,
        input: OcrInput,
        confidence: MutableMap<String, Double>,
    ): GradedInfo {
        val upperAll = all.uppercase()
        confidence["graded.grading_company"] = 0.9

        // Cert: a numeric barcode payload beats OCR digits.
        val barcodeCert = input.barcodes.firstOrNull { it.matches(Regex("\\d{7,10}")) }
        val cert = barcodeCert
            ?: certRegex.findAll(upperAll).map { it.value }.maxByOrNull { it.length }
        cert?.let { confidence["graded.cert_number"] = if (barcodeCert != null) 0.95 else 0.8 }

        val gradeMatch = gradeWordNum.find(upperAll) ?: gradeNumWord.find(upperAll)
        val gradeLabel = gradeMatch?.value?.replace(Regex("\\s+"), " ")?.trim()
        val grade = gradeMatch?.groupValues?.firstNotNullOfOrNull { it.toDoubleOrNull() }
        grade?.let {
            confidence["graded.grade"] = 0.85
            confidence["graded.grade_label"] = 0.85
        }

        val subValues = subgradeNames.associateWith { name ->
            Regex("$name\\s+($GRADE_NUM)").find(upperAll)?.groupValues?.get(1)?.toDoubleOrNull()
        }
        val subgrades = if (subValues.values.any { it != null }) {
            Subgrades(
                centering = subValues["CENTERING"],
                corners = subValues["CORNERS"],
                edges = subValues["EDGES"],
                surface = subValues["SURFACE"],
            )
        } else null

        val autographGrade = autographGradeRegex.find(upperAll)
            ?.groupValues?.get(1)?.toDoubleOrNull()
        autographGrade?.let { confidence["graded.autograph_grade"] = 0.8 }

        // Description: the label line carrying the year (e.g. "2000 UPPER DECK"),
        // plus the following line when it looks like the subject.
        val labelLines = labelFace.lines().map { it.trim() }.filter { it.isNotEmpty() }
        val yearLineIdx = labelLines.indexOfFirst { yearRegex.containsMatchIn(it) }
        val description = if (yearLineIdx >= 0) {
            val next = labelLines.getOrNull(yearLineIdx + 1)
            listOfNotNull(labelLines[yearLineIdx], next).joinToString(" ").trim()
        } else null
        description?.let { confidence["graded.description"] = 0.5 }

        return GradedInfo(
            gradingCompany = company,
            grade = grade,
            gradeLabel = gradeLabel,
            description = description,
            subgrades = subgrades,
            autographGrade = autographGrade,
            certNumber = cert,
            labelText = labelFace.ifEmpty { null },
        )
    }

    // -- helpers -------------------------------------------------------------

    private fun String.containsCompany(): Boolean =
        Reference.gradingCompanies.keys.any { Regex("\\b$it\\b").containsMatchIn(this) }

    /** Returns (serialNumber, serialLimit, confidence) for the best candidate. */
    private fun findSerial(all: String): Triple<String, String, Double>? {
        var best: Triple<String, String, Double>? = null
        var bestScore = Int.MIN_VALUE
        for (line in all.lines()) {
            val upperLine = line.uppercase()
            for (match in serialRegex.findAll(line)) {
                val (num, limit) = match.destructured
                if (num.toInt() > limit.toInt() || limit.toInt() == 0) continue
                var score = 0
                if (line.trim() == match.value) score += 3 // stamped on its own line
                if (num.length > 1 && num.startsWith("0")) score += 1 // zero-padded copy number
                // COA prose like "worn by X on 5/19 at the 2007 ..." is a date, not a serial
                if (Regex("\\b(ON|WORN|USED|PREMIERE|GAME)\\b").containsMatchIn(upperLine)) score -= 4
                if (score > bestScore) {
                    bestScore = score
                    best = Triple(num, limit, if (score >= 3) 0.85 else 0.55)
                }
            }
        }
        return if (bestScore >= 0) best else null
    }

    private fun findCardNumber(upper: String): String? {
        hashNumberRegex.find(upper)?.let { return it.groupValues[1] }
        cardNoRegex.find(upper)?.let { return it.groupValues[1] }
        return prefixedNumberRegex.findAll(upper)
            .map { it.groupValues[1] }
            .firstOrNull { it !in gradeCompoundWords }
    }

    /** A player name line: 2-3 plain word tokens, no digits, no known vocabulary. */
    private fun findPlayerName(all: String): String? {
        for (rawLine in all.lines()) {
            // Labels often prefix the subject with the card number ("#308 CALVIN JOHNSON").
            val line = rawLine.trim().replace(Regex("^#\\s?[A-Z0-9-]+\\s+"), "")
            val tokens = line.split(Regex("\\s+"))
            if (tokens.size !in 2..3) continue
            if (tokens.any { !nameToken.matches(it) }) continue
            if (tokens.any { it.uppercase().trimEnd('.', ',') in Reference.nameStopWords }) continue
            if (tokens.any { it.uppercase() in Reference.gradingCompanies.keys }) continue
            if (tokens.any { it.uppercase() in Reference.teamWords }) continue
            val upperLine = line.uppercase()
            if (Reference.sets.keys.any { upperLine.contains(it) }) continue
            if (Reference.brands.keys.any { upperLine.contains(it) }) continue
            return tokens.joinToString(" ") { token ->
                token.lowercase().replaceFirstChar { it.uppercase() }
            }
        }
        return null
    }

    /** A team line ends in a known nickname ("DETROIT LIONS", "QUARTERBACK ATLANTA FALCONS"). */
    private fun findTeam(all: String): String? {
        for (rawLine in all.lines()) {
            val tokens = rawLine.trim().split(Regex("\\s+")).filter { it.isNotEmpty() }
            if (tokens.size !in 1..4) continue
            if (tokens.last().uppercase().trimEnd('.', ',') !in Reference.teamWords) continue
            val kept = tokens.filter { it.uppercase().trimEnd('.', ',') !in Reference.nameStopWords }
            if (kept.isEmpty()) continue
            return kept.joinToString(" ") { token ->
                token.lowercase().replaceFirstChar { it.uppercase() }
            }
        }
        return null
    }

    private fun nowIso(): String = java.time.Instant.now().toString()
}
