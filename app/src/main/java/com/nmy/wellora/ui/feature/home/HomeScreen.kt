package com.nmy.wellora.ui.feature.home

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Accessibility
import androidx.compose.material.icons.filled.AccountCircle
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.material.icons.filled.CheckBox
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.DocumentScanner
import androidx.compose.material.icons.filled.Event
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.HealthAndSafety
import androidx.compose.material.icons.filled.Apartment
import androidx.compose.material.icons.filled.MonitorHeart
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.NotificationsNone
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Science
import androidx.compose.material.icons.automirrored.filled.Article
import androidx.compose.material.icons.automirrored.filled.Chat
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.IconButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
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
import androidx.compose.ui.unit.sp
import com.nmy.wellora.ui.theme.WelloraBackground
import com.nmy.wellora.ui.theme.WelloraIconBlue
import com.nmy.wellora.ui.theme.WelloraMutedText
import com.nmy.wellora.ui.theme.WelloraPrimary
import com.nmy.wellora.ui.theme.WelloraPrimaryDark
import com.nmy.wellora.ui.theme.WelloraPrimaryContainer
import com.nmy.wellora.ui.theme.WelloraSoftBlue
import com.nmy.wellora.ui.theme.WelloraSurface
import com.nmy.wellora.ui.theme.WelloraText

@Composable
fun HomeScreen(
    seniorMode: Boolean,
    onToggleMode: () -> Unit,
    onOpenDestination: (HomeAction) -> Unit,
    modifier: Modifier = Modifier
) {
    val titleSize = if (seniorMode) 30.sp else 26.sp
    val cardTitleSize = if (seniorMode) 20.sp else 18.sp
    val bodySize = if (seniorMode) 18.sp else 14.sp

    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(WelloraBackground)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Surface(
                modifier = Modifier.size(40.dp),
                shape = RoundedCornerShape(12.dp),
                color = WelloraPrimary
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        imageVector = Icons.Default.HealthAndSafety,
                        contentDescription = "知安",
                        tint = Color.White,
                        modifier = Modifier.size(24.dp)
                    )
                }
            }
            Text(
                text = "Home",
                style = MaterialTheme.typography.titleLarge,
                color = WelloraText,
                modifier = Modifier.weight(1f)
            )
            IconButton(onClick = { onOpenDestination(HomeAction.Tasks) }, modifier = Modifier.semantics { contentDescription = "查看消息" }) {
                Icon(Icons.Default.NotificationsNone, contentDescription = null, tint = WelloraText)
            }
            IconButton(onClick = { onOpenDestination(HomeAction.Account) }, modifier = Modifier.semantics { contentDescription = "打开我的" }) {
                Icon(Icons.Default.AccountCircle, contentDescription = null, tint = WelloraPrimary)
            }
        }

        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text("示例资料 · 今天状态良好", color = WelloraMutedText, fontSize = bodySize)
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "下午好，小林",
                    color = WelloraText,
                    fontSize = titleSize,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.weight(1f)
                )
                FilledTonalButton(
                    onClick = onToggleMode,
                    shape = RoundedCornerShape(24.dp),
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Accessibility,
                        contentDescription = null,
                        modifier = Modifier.size(21.dp)
                    )
                    Spacer(Modifier.width(6.dp))
                    Text(if (seniorMode) "标准模式" else "长辈模式", fontSize = 14.sp)
                }
            }
        }

        Surface(
            onClick = { onOpenDestination(HomeAction.Consultation) },
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp)
                .semantics {
                    role = Role.Button
                    contentDescription = "打开健康咨询，想了解什么健康问题"
                },
            shape = RoundedCornerShape(20.dp),
            color = WelloraSurface,
            shadowElevation = 1.dp
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 18.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Default.Search, contentDescription = null, tint = WelloraMutedText, modifier = Modifier.size(32.dp))
                Spacer(Modifier.width(14.dp))
                Text("想了解什么健康问题？", color = WelloraMutedText, fontSize = bodySize, modifier = Modifier.weight(1f))
                Surface(shape = RoundedCornerShape(50), color = WelloraIconBlue, modifier = Modifier.size(48.dp)) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(Icons.Default.Mic, contentDescription = "语音咨询", tint = WelloraPrimary, modifier = Modifier.size(27.dp))
                    }
                }
            }
        }

        Row(horizontalArrangement = Arrangement.spacedBy(16.dp), modifier = Modifier.fillMaxWidth()) {
            FeatureCard(
                title = "上传报告", subtitle = "拍照上传 检测识别", icon = Icons.Default.DocumentScanner,
                titleSize = cardTitleSize, bodySize = bodySize, modifier = Modifier.weight(1f),
                onClick = { onOpenDestination(HomeAction.UploadReport) }
            )
            FeatureCard(
                title = "报告对比", subtitle = "多次报告 对比分析", icon = Icons.Default.BarChart,
                titleSize = cardTitleSize, bodySize = bodySize, modifier = Modifier.weight(1f),
                onClick = { onOpenDestination(HomeAction.ReportCompare) }
            )
        }
        Row(horizontalArrangement = Arrangement.spacedBy(16.dp), modifier = Modifier.fillMaxWidth()) {
            FeatureCard(
                title = "健康咨询", subtitle = "健康问题 智能解答", icon = Icons.AutoMirrored.Filled.Chat,
                titleSize = cardTitleSize, bodySize = bodySize, modifier = Modifier.weight(1f),
                onClick = { onOpenDestination(HomeAction.Consultation) }
            )
            FeatureCard(
                title = "科室参考", subtitle = "根据情况 推荐科室", icon = Icons.Default.Apartment,
                titleSize = cardTitleSize, bodySize = bodySize, modifier = Modifier.weight(1f),
                onClick = { onOpenDestination(HomeAction.DepartmentGuide) }
            )
        }

        Surface(
            onClick = { onOpenDestination(HomeAction.ReportCompare) },
            modifier = Modifier.fillMaxWidth().semantics { contentDescription = "健康小结示例，近30日生化指标处于平稳区间" },
            shape = RoundedCornerShape(20.dp),
            color = WelloraPrimary,
            contentColor = Color.White
        ) {
            Row(modifier = Modifier.padding(horizontal = 20.dp, vertical = 16.dp), verticalAlignment = Alignment.CenterVertically) {
                Surface(shape = RoundedCornerShape(50), color = WelloraPrimaryDark.copy(alpha = 0.55f), modifier = Modifier.size(52.dp)) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(Icons.Default.MonitorHeart, contentDescription = null, tint = Color.White, modifier = Modifier.size(28.dp))
                    }
                }
                Spacer(Modifier.width(14.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text("健康小结", fontSize = 15.sp, fontWeight = FontWeight.Bold, color = Color.White)
                    Text("近30日生化指标处于平稳区间", fontSize = bodySize, color = Color.White)
                }
                Icon(Icons.Default.ChevronRight, contentDescription = "查看健康小结", tint = Color.White, modifier = Modifier.size(30.dp))
            }
        }

        SectionHeader(title = "最近报告", action = "查看全部", onClick = { onOpenDestination(HomeAction.Records) })
        ReportRow("体检报告 · 示例", "10月28日 · 三甲体检中心", "已确认", Icons.AutoMirrored.Filled.Article, WelloraPrimaryContainer) {
            onOpenDestination(HomeAction.ReportDetail)
        }
        ReportRow("检验报告 · 示例", "10月29日 · 血液生化全项", "待核对", Icons.Default.Science, WelloraIconBlue) {
            onOpenDestination(HomeAction.ReportReview)
        }

        SectionHeader(title = "今日待办", action = "2项需关注", onClick = { onOpenDestination(HomeAction.Tasks) })
        TodoRow("核对一份报告", "请确认报告信息是否完整", Icons.Default.CheckBox) { onOpenDestination(HomeAction.ReportReview) }
        TodoRow("查看复诊提醒", "已有1条复诊提醒", Icons.Default.Event) { onOpenDestination(HomeAction.Followup) }

        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(18.dp),
            color = WelloraSoftBlue
        ) {
            Row(modifier = Modifier.padding(18.dp), verticalAlignment = Alignment.Top) {
                Surface(shape = RoundedCornerShape(50), color = WelloraPrimaryContainer, modifier = Modifier.size(48.dp)) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(Icons.Default.Lightbulb, contentDescription = null, tint = WelloraPrimary, modifier = Modifier.size(26.dp))
                    }
                }
                Spacer(Modifier.width(14.dp))
                Column {
                    Text("健康小贴士", fontWeight = FontWeight.Bold, fontSize = 17.sp, color = WelloraText)
                    Spacer(Modifier.height(4.dp))
                    Text("示例：体检准备请以医疗机构的具体要求为准。", color = WelloraText, fontSize = bodySize, lineHeight = (bodySize.value + 8).sp)
                }
            }
        }
        Spacer(Modifier.height(8.dp))
    }
}

enum class HomeAction {
    Account, Records, UploadReport, ReportCompare, Consultation, DepartmentGuide,
    ReportDetail, ReportReview, Tasks, Followup
}

@Composable
private fun FeatureCard(
    title: String,
    subtitle: String,
    icon: ImageVector,
    titleSize: androidx.compose.ui.unit.TextUnit,
    bodySize: androidx.compose.ui.unit.TextUnit,
    modifier: Modifier,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = modifier.height(128.dp).semantics { contentDescription = "$title：$subtitle" },
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = WelloraSurface),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth().padding(12.dp)) {
            Surface(shape = RoundedCornerShape(50), color = WelloraIconBlue, modifier = Modifier.size(48.dp)) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(icon, contentDescription = null, tint = WelloraPrimary, modifier = Modifier.size(26.dp))
                }
            }
            Spacer(Modifier.height(6.dp))
            Text(title, fontSize = titleSize, fontWeight = FontWeight.Bold, color = WelloraText)
            Spacer(Modifier.height(4.dp))
            Text(subtitle, fontSize = bodySize, color = WelloraMutedText)
        }
    }
}

@Composable
private fun SectionHeader(title: String, action: String, onClick: () -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
        Text(title, style = MaterialTheme.typography.titleLarge, color = WelloraText, modifier = Modifier.weight(1f))
        Row(
            modifier = Modifier
                .clickable(onClick = onClick)
                .semantics { role = Role.Button; contentDescription = "${action}：$title" }
                .padding(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(action, color = WelloraMutedText, fontSize = 16.sp)
            Icon(Icons.Default.ChevronRight, contentDescription = null, tint = WelloraMutedText)
        }
    }
}

@Composable
private fun ReportRow(title: String, subtitle: String, status: String, icon: ImageVector, iconColor: Color, onClick: () -> Unit) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth().semantics { contentDescription = "$title，$subtitle，状态$status" },
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = WelloraSurface),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Row(modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp), verticalAlignment = Alignment.CenterVertically) {
            Surface(shape = RoundedCornerShape(10.dp), color = iconColor, modifier = Modifier.size(44.dp)) {
                Box(contentAlignment = Alignment.Center) { Icon(icon, contentDescription = null, tint = WelloraPrimary, modifier = Modifier.size(28.dp)) }
            }
            Spacer(Modifier.width(14.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(title, fontSize = 16.sp, fontWeight = FontWeight.SemiBold, color = WelloraText)
                Text(subtitle, fontSize = 14.sp, color = WelloraMutedText)
            }
            Surface(shape = RoundedCornerShape(20.dp), color = if (status == "已确认") WelloraPrimaryContainer else WelloraIconBlue) {
                Text(status, color = WelloraPrimary, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp))
            }
            Icon(Icons.Default.ChevronRight, contentDescription = "打开$title", tint = WelloraMutedText, modifier = Modifier.size(28.dp))
        }
    }
}

@Composable
private fun TodoRow(title: String, subtitle: String, icon: ImageVector, onClick: () -> Unit) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth().semantics { contentDescription = "$title：$subtitle" },
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = WelloraSurface),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Row(modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp), verticalAlignment = Alignment.CenterVertically) {
            Surface(shape = RoundedCornerShape(10.dp), color = WelloraIconBlue, modifier = Modifier.size(44.dp)) {
                Box(contentAlignment = Alignment.Center) { Icon(icon, contentDescription = null, tint = WelloraPrimary, modifier = Modifier.size(28.dp)) }
            }
            Spacer(Modifier.width(14.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(title, fontSize = 16.sp, fontWeight = FontWeight.SemiBold, color = WelloraText)
                Text(subtitle, fontSize = 14.sp, color = WelloraMutedText)
            }
            Icon(Icons.Default.ChevronRight, contentDescription = "打开$title", tint = WelloraMutedText, modifier = Modifier.size(28.dp))
        }
    }
}
