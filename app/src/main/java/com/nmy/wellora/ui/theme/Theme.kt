package com.nmy.wellora.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkColorScheme = darkColorScheme(
    primary = WelloraPrimaryContainer,
    onPrimary = WelloraText,
    secondary = WelloraPrimaryContainer,
    onSecondary = WelloraText,
    background = Color(0xFF101513),
    surface = Color(0xFF101513),
    onBackground = Color(0xFFE7F0EC),
    onSurface = Color(0xFFE7F0EC)
)

private val LightColorScheme = lightColorScheme(
    primary = WelloraPrimary,
    onPrimary = Color.White,
    primaryContainer = WelloraPrimaryContainer,
    onPrimaryContainer = WelloraText,
    secondary = WelloraPrimary,
    onSecondary = Color.White,
    secondaryContainer = WelloraPrimaryContainer,
    onSecondaryContainer = WelloraText,
    background = WelloraBackground,
    surface = WelloraSurface,
    onBackground = WelloraText,
    onSurface = WelloraText,
    outline = WelloraBorder
)

@Composable
fun WelloraTheme(
    darkTheme: Boolean = false,
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
