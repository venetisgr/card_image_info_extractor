package com.cardextractor.parser

import com.cardextractor.model.CardType
import com.cardextractor.model.GradingCompany
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

/**
 * Fixtures approximate ML Kit output for the owner's real cards
 * (data/images/seed) — the same cards the cloud engine was evaluated on.
 */
class OcrCardParserTest {

    private fun parse(front: String? = null, back: String? = null, barcodes: List<String> = emptyList()) =
        OcrCardParser.parse(
            OcrInput(front, back, barcodes, listOf("test:front")),
            timestamp = "2026-07-06T12:00:00Z",
        )

    // -- 2000 Upper Deck Tom Brady #254, PSA EX-MT 6 -------------------------

    @Test
    fun `psa slab label parses company grade cert and identity`() {
        val card = parse(
            front = """
                PSA
                2000 UPPER DECK
                TOM BRADY
                #254
                EX-MT 6
                111281750
            """.trimIndent(),
        )
        assertEquals(CardType.Graded, card.cardType)
        assertEquals(GradingCompany.PSA, card.graded?.gradingCompany)
        assertEquals(6.0, card.graded?.grade)
        assertEquals("EX-MT 6", card.graded?.gradeLabel)
        assertEquals("111281750", card.graded?.certNumber)
        assertEquals("2000", card.year)
        assertEquals("Upper Deck", card.brand)
        assertEquals("254", card.cardNumber)
        assertEquals("Tom Brady", card.playerName)
        assertEquals("2000 UPPER DECK TOM BRADY", card.graded?.description)
        assertTrue(card.perFieldConfidence.containsKey("graded.cert_number"))
    }

    // -- 2007 Leaf Limited CJ #308, BGS 9 + subgrades + AUTOGRAPH 10, 1/1 -----

    @Test
    fun `bgs slab with subgrades autograph grade and one-of-one serial`() {
        val card = parse(
            front = """
                2007 LEAF LIMITED
                COLLEGE PHENOMS AUTOS
                PLATINUM SPOTLIGHT
                #308 CALVIN JOHNSON
                9 MINT
                CENTERING 9 CORNERS 8.5
                EDGES 9 SURFACE 9
                0018180806
                BECKETT 10 AUTOGRAPH
            """.trimIndent(),
            back = """
                308
                1/1
                © 2007 DONRUSS PLAYOFF L.P. PRINTED IN THE USA.
            """.trimIndent(),
        )
        assertEquals(CardType.Graded, card.cardType)
        assertEquals(GradingCompany.Bgs, card.graded?.gradingCompany)
        assertEquals(9.0, card.graded?.grade)
        assertEquals(8.5, card.graded?.subgrades?.corners)
        assertEquals(9.0, card.graded?.subgrades?.surface)
        assertEquals(10.0, card.graded?.autographGrade)
        assertEquals("0018180806", card.graded?.certNumber)
        assertEquals("1", card.attributes.serialNumber)
        assertEquals("1", card.attributes.serialLimit)
        assertEquals("Leaf Limited", card.set)
        assertEquals("Leaf", card.brand)
        assertEquals("308", card.cardNumber)
        assertEquals("Calvin Johnson", card.playerName)
        assertEquals("2007", card.year)
    }

    // -- 2010 Contenders Demaryius #209, PSA GEM MT 10 ------------------------

    @Test
    fun `gem mint ten with barcode cert and sport from nfl token`() {
        val card = parse(
            front = """
                PSA
                2010 PLAYOFF CONTENDERS #209
                DEMARYIUS THOMAS
                RUSH/LOOK.FORWARD - AUTO.
                GEM MT 10
                20505941
            """.trimIndent(),
            back = """
                CARD NO. 209
                BRONCOS
                NFL PLAYERS
                © 2010 PANINI AMERICA, INC.
            """.trimIndent(),
            barcodes = listOf("20505941"),
        )
        assertEquals(10.0, card.graded?.grade)
        assertEquals("GEM MT 10", card.graded?.gradeLabel)
        assertEquals("20505941", card.graded?.certNumber)
        assertEquals(0.95, card.perFieldConfidence["graded.cert_number"])
        assertEquals("Playoff Contenders", card.set)
        assertEquals("Panini", card.brand)
        assertEquals("209", card.cardNumber)
        assertEquals("Demaryius Thomas", card.playerName)
        assertEquals(com.cardextractor.model.Sport.Football, card.sport)
        assertEquals(true, card.autograph?.present)
        // "RUSH/LOOK.FORWARD" must not be mistaken for serial numbering
        assertNull(card.attributes.serialNumber)
    }

    // -- 2007 NT Calvin Johnson jersey, RAW in a one-touch --------------------

    @Test
    fun `raw card with coa is not graded and serial beats coa date`() {
        val card = parse(
            front = """
                PLAYOFF
                DETROIT LIONS
                ROOKIE WR
                CALVIN JOHNSON
                AUTHENTIC EVENT-WORN JERSEY
                NATIONAL TREASURES
            """.trimIndent(),
            back = """
                107
                05/99
                CERTIFICATE OF AUTHENTICITY
                The enclosed piece of jersey was cut from an Authentic Jersey
                personally worn by Calvin Johnson on 5/19 at the 2007 NFL Players
                Rookie Premiere. The authentic autograph is an official autograph
                signed by Calvin Johnson and is guaranteed by Donruss Playoff L.P.
            """.trimIndent(),
        )
        assertEquals(CardType.Raw, card.cardType)
        assertNull(card.graded)
        // the stamped 05/99 wins; the COA's "on 5/19" date is rejected
        assertEquals("05", card.attributes.serialNumber)
        assertEquals("99", card.attributes.serialLimit)
        assertEquals("National Treasures", card.set)
        assertEquals("Playoff", card.brand)
        assertEquals("Calvin Johnson", card.playerName)
        assertEquals("Detroit Lions", card.team)
        assertEquals(true, card.memorabilia?.present)
        assertEquals(true, card.autograph?.present) // COA: "official autograph signed by"
    }

    // -- 2008 Topps Matt Ryan, BGS slab photographed from the BACK ------------

    @Test
    fun `beckett branding on slab back means graded with unknown grade`() {
        val card = parse(
            front = """
                THE WORLD'S MOST TRUSTED
                SOURCE IN COLLECTING
                BECKETT GRADING SERVICES
                TOPPS
                MATT RYAN
                QUARTERBACK ATLANTA FALCONS
                RPA-MR
                COMPLETE COLLEGE PASSING RECORD
                BOSTON COLLEGE
                © 2008 THE TOPPS COMPANY, INC.
            """.trimIndent(),
        )
        assertEquals(CardType.Graded, card.cardType)
        assertEquals(GradingCompany.Bgs, card.graded?.gradingCompany)
        assertNull(card.graded?.grade)
        assertNull(card.graded?.certNumber)
        assertEquals("Topps", card.brand)
        assertEquals("2008", card.year)
        assertEquals("RPA-MR", card.cardNumber)
        assertEquals("Matt Ryan", card.playerName)
        assertEquals("Atlanta Falcons", card.team)
    }

    @Test
    fun `grade compounds are not mistaken for prefixed card numbers`() {
        val card = parse(front = "PSA\n1996 COLL. CHOICE INT'L\nMICHAEL JORDAN\nEX 5\n111281730")
        assertEquals(5.0, card.graded?.grade)
        assertEquals("EX 5", card.graded?.gradeLabel)
        assertEquals("Collector's Choice", card.set)
        assertEquals("Michael Jordan", card.playerName)
        assertNull(card.cardNumber) // no # token in this fixture; EX-MT style must not match
    }

    @Test
    fun `empty input yields a raw card with nulls`() {
        val card = parse(front = "")
        assertEquals(CardType.Raw, card.cardType)
        assertNull(card.playerName)
        assertNull(card.year)
        assertNotNull(card.provenance)
        assertEquals("android-parser-0.1.0", card.provenance.modelVersion)
    }
}
