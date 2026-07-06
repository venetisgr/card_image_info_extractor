package com.cardextractor.app.ui

import android.content.Context
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import com.cardextractor.app.MainViewModel
import com.cardextractor.app.extract.ExtractorMode
import java.io.File

private fun newCaptureUri(context: Context): Uri {
    val dir = File(context.cacheDir, "captures").apply { mkdirs() }
    val file = File.createTempFile("card_", ".jpg", dir)
    return FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
}

@Composable
fun CaptureScreen(viewModel: MainViewModel, modifier: Modifier = Modifier) {
    val state by viewModel.state.collectAsState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Scan a card", style = MaterialTheme.typography.headlineSmall)

        FaceRow("Front", state.frontUri) { viewModel.setFront(it) }
        FaceRow("Back (optional)", state.backUri) { viewModel.setBack(it) }

        // On-device vs cloud (Claude) — roadmap P3-8.
        SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
            SegmentedButton(
                selected = state.mode == ExtractorMode.ON_DEVICE,
                onClick = { viewModel.setMode(ExtractorMode.ON_DEVICE) },
                shape = SegmentedButtonDefaults.itemShape(0, 2),
            ) { Text("On-device") }
            SegmentedButton(
                selected = state.mode == ExtractorMode.CLOUD,
                onClick = { viewModel.setMode(ExtractorMode.CLOUD) },
                shape = SegmentedButtonDefaults.itemShape(1, 2),
            ) { Text("Cloud (Claude)") }
        }

        Button(
            onClick = viewModel::extract,
            enabled = !state.busy && state.frontUri != null,
            modifier = Modifier.fillMaxWidth(),
        ) {
            if (state.busy) {
                CircularProgressIndicator(Modifier.height(20.dp))
            } else {
                Text("Extract card info")
            }
        }

        state.error?.let {
            Text(it, color = MaterialTheme.colorScheme.error)
        }
        state.result?.let { card ->
            ResultCard(card, state.resultJson)
        }
        Spacer(Modifier.height(24.dp))
    }
}

@Composable
private fun FaceRow(label: String, uri: Uri?, onPicked: (Uri?) -> Unit) {
    var pendingCapture by remember { mutableStateOf<Uri?>(null) }

    val takePicture = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { ok ->
        onPicked(if (ok) pendingCapture else null)
    }
    val pickImage = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { picked ->
        picked?.let(onPicked)
    }

    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(label, style = MaterialTheme.typography.titleMedium)
            Text(
                if (uri != null) "✓ photo attached" else "no photo yet",
                style = MaterialTheme.typography.bodySmall,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                val context = androidx.compose.ui.platform.LocalContext.current
                OutlinedButton(onClick = {
                    val target = newCaptureUri(context)
                    pendingCapture = target
                    takePicture.launch(target)
                }) { Text("Camera") }
                OutlinedButton(onClick = { pickImage.launch("image/*") }) { Text("Gallery") }
            }
        }
    }
}
