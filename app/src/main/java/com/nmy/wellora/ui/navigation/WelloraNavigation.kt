package com.nmy.wellora.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Folder
import androidx.compose.material.icons.filled.Medication
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.vector.ImageVector
import com.nmy.wellora.ui.theme.WelloraPrimary
import com.nmy.wellora.ui.theme.WelloraPrimaryContainer

enum class WelloraDestination(val label: String, val icon: ImageVector) {
    Home("首页", Icons.Default.Home),
    Records("健康档案", Icons.Default.Folder),
    Medications("用药", Icons.Default.Medication),
    Account("我的", Icons.Default.Person)
}

@Composable
fun WelloraNavigationBar(
    currentDestination: WelloraDestination,
    onDestinationSelected: (WelloraDestination) -> Unit
) {
    NavigationBar(
        containerColor = androidx.compose.ui.graphics.Color.White,
        tonalElevation = androidx.compose.ui.unit.Dp.Hairline
    ) {
        WelloraDestination.entries.forEach { destination ->
            NavigationBarItem(
                selected = currentDestination == destination,
                onClick = { onDestinationSelected(destination) },
                icon = {
                    Icon(
                        imageVector = destination.icon,
                        contentDescription = destination.label
                    )
                },
                label = { Text(destination.label) },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = WelloraPrimary,
                    selectedTextColor = WelloraPrimary,
                    indicatorColor = WelloraPrimaryContainer,
                    unselectedIconColor = androidx.compose.ui.graphics.Color(0xFF4D5A55),
                    unselectedTextColor = androidx.compose.ui.graphics.Color(0xFF4D5A55)
                )
            )
        }
    }
}
