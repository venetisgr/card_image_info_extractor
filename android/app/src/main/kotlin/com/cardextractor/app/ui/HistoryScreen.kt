package com.cardextractor.app.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import com.cardextractor.app.MainViewModel
import java.text.DateFormat
import java.util.Date

/** Saved scans from Room (roadmap P3-6). */
@Composable
fun HistoryScreen(viewModel: MainViewModel, modifier: Modifier = Modifier) {
    val scans by viewModel.history.collectAsState(initial = emptyList())

    LazyColumn(modifier = modifier.fillMaxSize(), contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp)) {
        items(scans, key = { it.id }) { scan ->
            var expanded by remember { mutableStateOf(false) }
            Card(
                Modifier
                    .fillMaxWidth()
                    .padding(bottom = 8.dp)
                    .clickable { expanded = !expanded },
            ) {
                Column(Modifier.padding(12.dp)) {
                    Text(scan.summary, style = MaterialTheme.typography.titleMedium)
                    Text(
                        "${scan.cardType} · ${scan.engine} · " +
                            DateFormat.getDateTimeInstance().format(Date(scan.createdAt)),
                        style = MaterialTheme.typography.bodySmall,
                    )
                    if (expanded) {
                        Text(
                            scan.cardJson,
                            fontFamily = FontFamily.Monospace,
                            style = MaterialTheme.typography.bodySmall,
                            modifier = Modifier.padding(top = 8.dp),
                        )
                    }
                }
            }
        }
    }
}
