package com.nmy.wellora

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.lifecycle.ViewModelProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.nmy.wellora.ui.feature.home.HomeAction
import com.nmy.wellora.ui.feature.home.HomeScreen
import com.nmy.wellora.ui.feature.records.AccountScreen
import com.nmy.wellora.ui.feature.records.AccountPanel
import com.nmy.wellora.ui.feature.records.AccountViewModel
import com.nmy.wellora.ui.feature.records.BasicProfileSummary
import com.nmy.wellora.ui.feature.records.MedicationsScreen
import com.nmy.wellora.ui.feature.records.RecordsScreen
import com.nmy.wellora.ui.feature.shared.FeatureRouteScreen
import com.nmy.wellora.ui.navigation.WelloraDestination
import com.nmy.wellora.ui.navigation.WelloraNavigationBar
import com.nmy.wellora.ui.theme.WelloraTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val accountModel = ViewModelProvider(this)[AccountViewModel::class.java]
        setContent { WelloraTheme { WelloraApp(accountModel) } }
    }
}

enum class WelloraRoute(val title: String) {
    Home("首页"), Records("健康档案"), Medications("用药"), Account("我的"),
    Consultation("健康咨询"), UploadReport("添加健康记录"), ReportReview("报告核对"),
    ReportDetail("报告详情"), ReportCompare("指标对比"), DepartmentGuide("科室参考"),
    DisplayMode("显示模式"), Followup("复诊提醒"), Notifications("消息中心"),
    History("咨询历史"), Knowledge("健康科普"), Privacy("隐私与安全"),
    Family("家属协助"), Backup("备份与恢复")
}

@Composable
private fun WelloraApp(accountModel: AccountViewModel) {
    val accountState by accountModel.state.collectAsState()
    var route by rememberSaveable { mutableStateOf(WelloraRoute.Home) }
    var seniorMode by rememberSaveable { mutableStateOf(false) }
    var completedUpload by rememberSaveable { mutableStateOf(false) }

    val open: (WelloraRoute) -> Unit = { route = it }
    val openHomeAction: (HomeAction) -> Unit = { action ->
        route = when (action) {
            HomeAction.Account -> WelloraRoute.Account
            HomeAction.Records -> WelloraRoute.Records
            HomeAction.UploadReport -> WelloraRoute.UploadReport
            HomeAction.ReportCompare -> WelloraRoute.ReportCompare
            HomeAction.Consultation -> WelloraRoute.Consultation
            HomeAction.DepartmentGuide -> WelloraRoute.DepartmentGuide
            HomeAction.ReportDetail -> WelloraRoute.ReportDetail
            HomeAction.ReportReview -> WelloraRoute.ReportReview
            HomeAction.Tasks -> WelloraRoute.Notifications
            HomeAction.Followup -> WelloraRoute.Followup
        }
    }

    val primary = when (route) {
        WelloraRoute.Home -> WelloraDestination.Home
        WelloraRoute.Records -> WelloraDestination.Records
        WelloraRoute.Medications -> WelloraDestination.Medications
        WelloraRoute.Account -> WelloraDestination.Account
        else -> null
    }

    Scaffold(
        bottomBar = {
            if (primary != null) {
                WelloraNavigationBar(currentDestination = primary, seniorMode = seniorMode, onDestinationSelected = {
                    route = when (it) {
                        WelloraDestination.Home -> WelloraRoute.Home
                        WelloraDestination.Records -> WelloraRoute.Records
                        WelloraDestination.Medications -> WelloraRoute.Medications
                        WelloraDestination.Account -> WelloraRoute.Account
                    }
                })
            }
        }
    ) { innerPadding ->
        when (route) {
            WelloraRoute.Home -> HomeScreen(seniorMode, { seniorMode = !seniorMode }, openHomeAction, Modifier.fillMaxSize().padding(innerPadding))
            WelloraRoute.Records -> RecordsScreen(seniorMode, completedUpload, open, Modifier.fillMaxSize().padding(innerPadding), profileContent = { BasicProfileSummary(accountState) { route = WelloraRoute.Account } })
            WelloraRoute.Medications -> MedicationsScreen(seniorMode, open, Modifier.fillMaxSize().padding(innerPadding))
            WelloraRoute.Account -> AccountScreen(seniorMode, { seniorMode = !seniorMode }, open, Modifier.fillMaxSize().padding(innerPadding), accountContent = { AccountPanel(accountModel, seniorMode) })
            else -> FeatureRouteScreen(
                route = route,
                seniorMode = seniorMode,
                completedUpload = completedUpload,
                onUploadCompleted = { completedUpload = true },
                onSeniorModeChanged = { seniorMode = it },
                onOpen = open,
                onBack = { route = WelloraRoute.Home },
                modifier = Modifier.fillMaxSize().padding(innerPadding)
            )
        }
    }
}
