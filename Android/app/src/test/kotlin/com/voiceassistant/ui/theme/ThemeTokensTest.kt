package com.voiceassistant.ui.theme

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class ThemeTokensTest {
    @Test
    fun `light scheme matches design tokens`() {
        assertEquals(Color(0xFF205FFF), LightColors.primary)
        assertEquals(Color(0xFFF5F6F7), LightColors.background)
        assertEquals(Color(0xFFFFFFFF), LightColors.surface)
        assertEquals(Color(0xFF0A0A0A), LightColors.onBackground)
        assertEquals(Color(0xFFAA55FF), LightColors.tertiary)
    }

    @Test
    fun `dark scheme matches design tokens`() {
        assertEquals(Color(0xFF8CAAFF), DarkColors.primary)
        assertEquals(Color(0xFF0A0A0A), DarkColors.background)
        assertEquals(Color(0xFF1A1A1A), DarkColors.surface)
        assertEquals(Color(0xFFF5F6F7), DarkColors.onBackground)
        assertEquals(Color(0xFFC58BFF), DarkColors.tertiary)
    }

    @Test
    fun `radii match design`() {
        assertEquals(16.dp, CardRadius)
        assertEquals(18.dp, MicRadius)
        assertEquals(28.dp, SheetRadius)
    }
}
