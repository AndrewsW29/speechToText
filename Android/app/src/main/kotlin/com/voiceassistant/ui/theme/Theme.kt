package com.voiceassistant.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.runtime.Composable
import androidx.compose.ui.unit.dp

val CardRadius = 16.dp
val MicRadius = 18.dp
val SheetRadius = 28.dp

val AppShapes = Shapes(
    medium = RoundedCornerShape(CardRadius),
    large = RoundedCornerShape(MicRadius),
    extraLarge = RoundedCornerShape(topStart = SheetRadius, topEnd = SheetRadius),
)

@Composable
fun VoiceAssistantTheme(darkTheme: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        typography = AppTypography,
        shapes = AppShapes,
        content = content,
    )
}
