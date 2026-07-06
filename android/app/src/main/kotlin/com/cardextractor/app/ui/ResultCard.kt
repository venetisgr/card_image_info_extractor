package com.cardextractor.app.ui

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import com.cardextractor.model.CardInfo

/** Key extracted fields + the full canonical JSON. */
@Composable
fun ResultCard(card: CardInfo, prettyJson: String?) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp)) {
            Text(
                card.playerName ?: "Unknown player",
                style = MaterialTheme.typography.titleLarge,
            )
            Text(
                listOfNotNull(card.year, card.brand, card.set, card.subset)
                    .joinToString(" · ")
                    .ifEmpty { "—" },
            )
            val graded = card.graded
            Text(
                if (graded != null) {
                    listOfNotNull(
                        graded.gradingCompany?.value,
                        graded.gradeLabel ?: graded.grade?.toString(),
                        graded.certNumber?.let { "cert $it" },
                    ).joinToString(" ")
                } else {
                    "raw (ungraded)"
                },
                style = MaterialTheme.typography.bodyMedium,
            )
            card.attributes.serialNumber?.let { sn ->
                Text("serial $sn/${card.attributes.serialLimit ?: "?"}")
            }
            if (card.autograph?.present == true) {
                Text("autograph" + (card.autograph?.inkColor?.let { " ($it ink)" } ?: ""))
            }
            if (card.memorabilia?.present == true) Text("memorabilia card")

            prettyJson?.let {
                Text(
                    it,
                    fontFamily = FontFamily.Monospace,
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier
                        .padding(top = 8.dp)
                        .horizontalScroll(rememberScrollState()),
                )
            }
        }
    }
}
