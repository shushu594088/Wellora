package com.nmy.wellora

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.nmy.wellora.ui.feature.home.HomeAction
import com.nmy.wellora.ui.feature.home.HomeScreen
import com.nmy.wellora.ui.navigation.WelloraDestination
import com.nmy.wellora.ui.navigation.WelloraNavigationBar
import com.nmy.wellora.ui.theme.WelloraTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            WelloraTheme {
                WelloraApp()
            }
        }
    }
}

@Composable
private fun WelloraApp() {
    var destination by rememberSaveable { mutableStateOf(WelloraDestination.Home) }
    var seniorMode by rememberSaveable { mutableStateOf(false) }
    var detailTitle by rememberSaveable { mutableStateOf<String?>(null) }

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        bottomBar = {
            if (detailTitle == null) {
                WelloraNavigationBar(
                    currentDestination = destination,
                    onDestinationSelected = {
                        detailTitle = null
                        destination = it
                    }
                )
            }
        }
    ) { innerPadding ->
        val currentDetail = detailTitle
        if (currentDetail != null) {
            ActionPlaceholder(
                title = currentDetail,
                modifier = Modifier.padding(innerPadding),
                onBack = { detailTitle = null }
            )
        } else {
            when (destination) {
                WelloraDestination.Home -> HomeScreen(
                    seniorMode = seniorMode,
                    onToggleMode = { seniorMode = !seniorMode },
                    onOpenDestination = { action ->
                        when (action) {
                            HomeAction.Account -> destination = WelloraDestination.Account
                            HomeAction.Records -> destination = WelloraDestination.Records
                            else -> detailTitle = action.label
                        }
                    },
                    modifier = Modifier.padding(innerPadding)
                )
                else -> DestinationPlaceholder(
                    destination = destination,
                    modifier = Modifier.padding(innerPadding),
                    onBack = { destination = WelloraDestination.Home }
                )
            }
        }
    }
}

private val HomeAction.label: String
    get() = when (this) {
        HomeAction.UploadReport -> "上传报告"
        HomeAction.ReportCompare -> "报告对比"
        HomeAction.Consultation -> "健康咨询"
        HomeAction.DepartmentGuide -> "科室参考"
        HomeAction.ReportDetail -> "报告详情"
        HomeAction.ReportReview -> "报告核对"
        HomeAction.Tasks -> "消息与待办"
        HomeAction.Followup -> "复诊提醒"
        HomeAction.Account -> "我的"
        HomeAction.Records -> "健康档案"
    }

@Composable
private fun ActionPlaceholder(title: String, modifier: Modifier = Modifier, onBack: () -> Unit) {
    Column(modifier = modifier.fillMaxSize().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
        Text(title, style = androidx.compose.material3.MaterialTheme.typography.headlineMedium)
        Text("此页面尚未实现；当前仅验证原生 Compose 导航。", modifier = Modifier.padding(top = 12.dp))
        androidx.compose.material3.TextButton(onClick = onBack, modifier = Modifier.padding(top = 20.dp)) {
            Text("返回首页")
        }
    }
}

@Composable
private fun DestinationPlaceholder(
    destination: WelloraDestination,
    modifier: Modifier = Modifier,
    onBack: () -> Unit
) {
    Column(
        modifier = modifier.fillMaxSize().padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(destination.label, style = androidx.compose.material3.MaterialTheme.typography.headlineMedium)
        Text("原生 Compose 路由已就绪，${destination.label}页面将在后续迭代实现。", modifier = Modifier.padding(top = 12.dp))
        androidx.compose.material3.TextButton(onClick = onBack, modifier = Modifier.padding(top = 20.dp)) {
            Text("返回首页")
        }
    }
}
