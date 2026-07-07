package com.cardextractor.parser

import com.cardextractor.model.GradingCompany
import com.cardextractor.model.Sport

/**
 * Bundled reference subset (roadmap P3-5): enough vocabulary to normalize the
 * common cases offline. The full checklist/normalization DB lives server-side.
 */
object Reference {

    /** Uppercase token -> grading company. */
    val gradingCompanies: Map<String, GradingCompany> = linkedMapOf(
        "PSA" to GradingCompany.PSA,
        "BECKETT" to GradingCompany.Bgs,
        "BGS" to GradingCompany.Bgs,
        "SGC" to GradingCompany.Sgc,
        "CGC" to GradingCompany.Cgc,
        "TAG" to GradingCompany.Tag,
    )

    /** Uppercase token -> canonical set name (longest tokens first). */
    val sets: Map<String, String> = linkedMapOf(
        "EXQUISITE COLLECTION" to "Exquisite Collection",
        "NATIONAL TREASURES" to "National Treasures",
        "PLAYOFF CONTENDERS" to "Playoff Contenders",
        "SP ROOKIE THREADS" to "SP Rookie Threads",
        "COLLECTOR'S CHOICE" to "Collector's Choice",
        "COLL. CHOICE" to "Collector's Choice",
        "GRIDIRON GEAR" to "Gridiron Gear",
        "LEAF LIMITED" to "Leaf Limited",
        "CONTENDERS" to "Playoff Contenders",
        "THREADS" to "Donruss Threads",
        "PRIZM" to "Prizm",
        "SELECT" to "Select",
        "MOSAIC" to "Mosaic",
        "OPTIC" to "Donruss Optic",
    )

    /** Canonical set -> brand, for when only the set name is printed. */
    val setToBrand: Map<String, String> = mapOf(
        "Exquisite Collection" to "Upper Deck",
        "National Treasures" to "Playoff",
        "Playoff Contenders" to "Panini",
        "SP Rookie Threads" to "Upper Deck",
        "Collector's Choice" to "Upper Deck",
        "Gridiron Gear" to "Donruss",
        "Leaf Limited" to "Leaf",
        "Threads" to "Donruss",
        "Prizm" to "Panini",
        "Select" to "Panini",
        "Mosaic" to "Panini",
        "Donruss Optic" to "Panini",
    )

    /** Uppercase token -> canonical brand name. */
    val brands: Map<String, String> = linkedMapOf(
        "UPPER DECK" to "Upper Deck",
        "TOPPS" to "Topps",
        "PANINI" to "Panini",
        "DONRUSS" to "Donruss",
        "BOWMAN" to "Bowman",
        "FLEER" to "Fleer",
        "LEAF" to "Leaf",
        "PLAYOFF" to "Playoff",
        "SCORE" to "Score",
    )

    /** League/word token -> sport. */
    val sportTokens: Map<String, Sport> = linkedMapOf(
        "NFL" to Sport.Football,
        "FOOTBALL" to Sport.Football,
        "NBA" to Sport.Basketball,
        "BASKETBALL" to Sport.Basketball,
        "MLB" to Sport.Baseball,
        "BASEBALL" to Sport.Baseball,
        "NHL" to Sport.Hockey,
        "HOCKEY" to Sport.Hockey,
        "SOCCER" to Sport.Soccer,
    )

    /** Team nicknames (last word of a team line). Excludes lines from player-name
     *  candidacy and drives `team` extraction. Subset — full rosters live server-side. */
    val teamWords: Set<String> = setOf(
        // NFL
        "LIONS", "BRONCOS", "PATRIOTS", "COWBOYS", "VIKINGS", "FALCONS", "EAGLES",
        "GIANTS", "JETS", "BEARS", "PACKERS", "STEELERS", "RAVENS", "CHIEFS",
        "RAIDERS", "CHARGERS", "SEAHAWKS", "TITANS", "COLTS", "TEXANS", "JAGUARS",
        "BILLS", "DOLPHINS", "BENGALS", "BROWNS", "SAINTS", "BUCCANEERS",
        "PANTHERS", "CARDINALS", "RAMS", "COMMANDERS",
        // NBA
        "BULLS", "CAVALIERS", "LAKERS", "CELTICS", "WARRIORS", "KNICKS", "HEAT",
        "SPURS", "SUNS", "MAVERICKS", "NUGGETS", "BUCKS", "ROCKETS", "THUNDER",
        // MLB
        "YANKEES", "DODGERS", "CUBS", "METS", "BRAVES", "ANGELS", "PADRES",
        "MARINERS", "ORIOLES", "ASTROS", "PHILLIES",
        // college (common on rookie-year memorabilia cards)
        "SOONERS", "JACKETS", "WOLVERINES", "BUCKEYES", "TIGERS", "GATORS",
        "SEMINOLES", "TROJANS", "LONGHORNS", "CRIMSON",
    )

    /** Words that disqualify a line from being a player name. */
    val nameStopWords: Set<String> = setOf(
        "ROOKIE", "TICKET", "AUTOGRAPH", "AUTO", "JERSEY", "PATCH", "RELIC",
        "MINT", "GEM", "AUTHENTIC", "CERTIFICATE", "AUTHENTICITY", "GRADING",
        "SERVICES", "COLLECTING", "TRUSTED", "SOURCE", "WORLD'S", "PLAYERS",
        "QUARTERBACK", "RECEIVER", "RUNNING", "CORNERS", "EDGES", "SURFACE",
        "CENTERING", "CARD", "COMPANY", "PRINTED", "DIVISION", "COLLECTORS",
        "UNIVERSE", "PROFESSIONAL", "SPORTS", "AUTHENTICATOR", "EDITION",
        "COLLEGE", "STATISTICS", "RECORD", "COMPLETE", "SPOTLIGHT", "PHENOMS",
        "PLATINUM", "LIMITED", "TREASURES", "NATIONAL", "GRIDIRON", "KINGS",
        "GEMS", "CONTENDERS", "PLAYOFF", "TOPPS", "PANINI", "DONRUSS", "FLEER",
        "BOWMAN", "LEAF", "UPPER", "DECK", "BECKETT", "SEASONS", "POSITION",
        "NUMBER", "ESTABLISHED",
    )
}
