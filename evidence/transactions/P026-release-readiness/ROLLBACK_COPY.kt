package com.nmy.wellora.ui.feature.shared

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.Cloud
import androidx.compose.material.icons.filled.ErrorOutline
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.nmy.wellora.ui.theme.WelloraBackground
import com.nmy.wellora.ui.theme.WelloraBorder
import com.nmy.wellora.ui.theme.WelloraIconBlue
import com.nmy.wellora.ui.theme.WelloraMutedText
import com.nmy.wellora.ui.theme.WelloraPrimary
import com.nmy.wellora.ui.theme.WelloraPrimaryDark
import com.nmy.wellora.ui.theme.WelloraPrimaryContainer
import com.nmy.wellora.ui.theme.WelloraSoftBlue
import com.nmy.wellora.ui.theme.WelloraSurface
import com.nmy.wellora.ui.theme.WelloraText

@Composable
fun PageColumn(
    modifier: Modifier = Modifier,
    seniorMode: Boolean = false,
    constrainWidth: Boolean = true,
    content: @Composable androidx.compose.foundation.layout.ColumnScope.() -> Unit
) {
    val gap = if (seniorMode) 24.dp else 16.dp
    BoxWithConstraints(modifier = modifier.fillMaxSize().background(WelloraBackground), contentAlignment = Alignment.TopCenter) {
        LazyColumn(
            modifier = (if (constrainWidth) Modifier.widthIn(max = 760.dp) else Modifier).fillMaxWidth().fillMaxSize(),
            contentPadding = PaddingValues(horizontal = if (seniorMode) 20.dp else 16.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.spacedBy(gap)
        ) { item { Column(verticalArrangement = Arrangement.spacedBy(gap), content = content) } }
    }
}

@Composable
fun PageHeader(title: String, subtitle: String? = null, onBack: (() -> Unit)? = null) {
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
        if (onBack != null) {
            IconButton(onClick = onBack, modifier = Modifier.semantics { contentDescription = "返回" }) { Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = null, tint = WelloraText) }
            Spacer(Modifier.width(4.dp))
        }
        Column(modifier = Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.titleLarge, color = WelloraText)
            if (subtitle != null) Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = WelloraMutedText)
        }
    }
}

@Composable
fun DemoBanner(text: String = "当前为离线演示，内容均为虚拟数据") {
    Surface(modifier = Modifier.fillMaxWidth().semantics { contentDescription = text }, shape = RoundedCornerShape(12.dp), color = WelloraSoftBlue, border = androidx.compose.foundation.BorderStroke(1.dp, WelloraBorder)) {
        Row(modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.Cloud, contentDescription = null, tint = WelloraPrimaryDark, modifier = Modifier.size(20.dp))
            Spacer(Modifier.width(10.dp))
            Text(text, color = WelloraText, style = MaterialTheme.typography.bodyMedium)
        }
    }
}

@Composable
fun SectionTitle(title: String, action: String? = null, onAction: (() -> Unit)? = null) {
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
        Text(title, style = MaterialTheme.typography.titleLarge, color = WelloraText, modifier = Modifier.weight(1f))
        if (action != null && onAction != null) TextButton(onClick = onAction) { Text(action, color = WelloraPrimary); Icon(Icons.Default.ChevronRight, contentDescription = null, tint = WelloraPrimary) }
    }
}

@Composable
fun GroupedPanel(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        color = WelloraSurface,
        shadowElevation = 1.dp
    ) {
        Column(content = content)
    }
}

@Composable
fun GroupedPanelRow(
    title: String,
    body: String? = null,
    icon: ImageVector = Icons.Default.Info,
    seniorMode: Boolean = false,
    trailing: (@Composable () -> Unit)? = null,
    onClick: (() -> Unit)? = null,
    showDivider: Boolean = true
) {
    val row: @Composable () -> Unit = {
        Row(
            modifier = Modifier.fillMaxWidth().heightIn(min = if (seniorMode) 84.dp else 68.dp).padding(horizontal = 18.dp, vertical = if (seniorMode) 14.dp else 10.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(icon, contentDescription = null, tint = WelloraPrimaryDark, modifier = Modifier.size(if (seniorMode) 28.dp else 22.dp))
            Spacer(Modifier.width(if (seniorMode) 18.dp else 14.dp))
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(title, style = if (seniorMode) MaterialTheme.typography.titleMedium else MaterialTheme.typography.bodyLarge, color = WelloraText)
                if (body != null) Text(body, style = MaterialTheme.typography.bodyMedium, color = WelloraMutedText)
            }
            trailing?.invoke()
            if (onClick != null) Icon(Icons.Default.ChevronRight, contentDescription = "打开$title", tint = WelloraMutedText, modifier = Modifier.size(if (seniorMode) 28.dp else 22.dp))
        }
    }
    if (onClick != null) {
        Surface(
            onClick = onClick,
            modifier = Modifier.fillMaxWidth().semantics { role = Role.Button; contentDescription = if (body == null) title else "$title：$body" },
            color = Color.Transparent
        ) { row() }
    } else {
        row()
    }
    if (showDivider) HorizontalDivider(modifier = Modifier.padding(horizontal = 18.dp), color = WelloraBackground)
}

@Composable
fun StatusChip(text: String, positive: Boolean = false, muted: Boolean = false) {
    val color = when { positive -> WelloraPrimaryContainer; muted -> WelloraSoftBlue; else -> WelloraIconBlue }
    val textColor = if (muted) WelloraMutedText else WelloraPrimaryDark
    Surface(shape = RoundedCornerShape(50), color = color, border = androidx.compose.foundation.BorderStroke(1.dp, WelloraBorder)) { Text(text, color = textColor, fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.labelLarge, modifier = Modifier.padding(horizontal = 12.dp, vertical = 7.dp)) }
}

@Composable
fun InfoCard(title: String, body: String, icon: ImageVector = Icons.Default.Info, modifier: Modifier = Modifier, trailing: (@Composable () -> Unit)? = null, onClick: (() -> Unit)? = null) {
    val content: @Composable () -> Unit = {
        Row(modifier = Modifier.padding(horizontal = 16.dp, vertical = 14.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(icon, contentDescription = null, tint = WelloraPrimaryDark, modifier = Modifier.size(22.dp))
            Spacer(Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) { Text(title, style = MaterialTheme.typography.titleMedium, color = WelloraText); Text(body, style = MaterialTheme.typography.bodyMedium, color = WelloraMutedText) }
            trailing?.invoke()
            if (onClick != null) Icon(Icons.Default.ChevronRight, contentDescription = "打开$title", tint = WelloraMutedText)
        }
    }
    val cardModifier = modifier.fillMaxWidth().then(if (onClick != null) Modifier.semantics { role = Role.Button; contentDescription = "$title：$body" } else Modifier)
    if (onClick != null) Card(onClick = onClick, modifier = cardModifier.heightIn(min = 72.dp), colors = CardDefaults.cardColors(WelloraSurface), shape = RoundedCornerShape(12.dp), border = androidx.compose.foundation.BorderStroke(1.dp, WelloraBorder), elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)) { content() }
    else Surface(modifier = cardModifier.heightIn(min = 72.dp), color = Color.Transparent) { content() }
}

@Composable
fun PrimaryButton(text: String, onClick: () -> Unit, modifier: Modifier = Modifier, enabled: Boolean = true) {
    Button(onClick = onClick, enabled = enabled, modifier = modifier.fillMaxWidth().heightIn(min = 48.dp), shape = RoundedCornerShape(8.dp), colors = ButtonDefaults.buttonColors(containerColor = com.nmy.wellora.ui.theme.WelloraAccent, contentColor = com.nmy.wellora.ui.theme.WelloraOnAccent)) { Text(text, fontWeight = FontWeight.SemiBold) }
}

@Composable
fun SecondaryButton(text: String, onClick: () -> Unit, modifier: Modifier = Modifier) {
    OutlinedButton(onClick = onClick, modifier = modifier.fillMaxWidth().heightIn(min = 48.dp), shape = RoundedCornerShape(8.dp), colors = ButtonDefaults.outlinedButtonColors(contentColor = WelloraPrimary)) { Text(text) }
}

@Composable
fun EmptyState(title: String, body: String, action: String? = null, onAction: (() -> Unit)? = null) {
    Surface(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp), color = WelloraSurface) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.padding(28.dp)) {
            Icon(Icons.Default.Info, contentDescription = null, tint = WelloraPrimary, modifier = Modifier.size(34.dp))
            Spacer(Modifier.height(10.dp)); Text(title, style = MaterialTheme.typography.titleMedium, color = WelloraText); Text(body, style = MaterialTheme.typography.bodyMedium, color = WelloraMutedText)
            if (action != null && onAction != null) TextButton(onClick = onAction) { Text(action) }
        }
    }
}

@Composable
fun LoadingErrorRow(error: Boolean = false, onRetry: () -> Unit) {
    Surface(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(12.dp), color = if (error) Color(0xFFFFF2F0) else WelloraSoftBlue) {
        Row(modifier = Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(if (error) Icons.Default.ErrorOutline else Icons.Default.Refresh, contentDescription = null, tint = if (error) Color(0xFFB3261E) else WelloraPrimary)
            Spacer(Modifier.width(10.dp)); Text(if (error) "示例任务失败，可重试" else "示例任务处理中…", modifier = Modifier.weight(1f), color = WelloraText); TextButton(onClick = onRetry) { Text(if (error) "重试" else "刷新") }
        }
    }
}

@Composable
fun ResponsiveTwoColumn(content: @Composable (Boolean) -> Unit) {
    BoxWithConstraints(modifier = Modifier.fillMaxWidth()) { content(maxWidth >= 600.dp) }
}

@Composable
fun MetricRow(label: String, value: String, unit: String, note: String, highlight: Boolean = false) {
    Row(modifier = Modifier.fillMaxWidth().padding(vertical = 9.dp), verticalAlignment = Alignment.CenterVertically) {
        Text(label, color = WelloraText, modifier = Modifier.weight(1.1f)); Text(value, color = if (highlight) WelloraPrimary else WelloraText, fontWeight = FontWeight.Bold, modifier = Modifier.weight(.65f)); Text(unit, color = WelloraMutedText, modifier = Modifier.weight(.55f)); Text(note, color = WelloraMutedText, modifier = Modifier.weight(.7f))
    }
}
