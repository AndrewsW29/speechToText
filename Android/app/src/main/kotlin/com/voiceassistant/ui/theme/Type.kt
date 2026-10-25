package com.voiceassistant.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.googlefonts.Font as GoogleFont
import androidx.compose.ui.text.googlefonts.GoogleFont as GoogleFontName
import androidx.compose.ui.unit.sp
import com.voiceassistant.R

// Heebo via downloadable fonts. Requires res/values/font_certs.xml (Android Studio wizard);
// see res/font/README.txt for bundling instead.
private val provider = GoogleFont.Provider(
    providerAuthority = "com.google.android.gms.fonts",
    providerPackage = "com.google.android.gms",
    certificates = R.array.com_google_android_gms_fonts_certs,
)
private val heebo = GoogleFontName("Heebo")

val HeeboFamily = FontFamily(
    GoogleFont(heebo, provider, FontWeight.Normal),
    GoogleFont(heebo, provider, FontWeight.Bold),
    GoogleFont(heebo, provider, FontWeight.ExtraBold),
)

val AppTypography = Typography(
    headlineMedium = TextStyle(HeeboFamily, FontWeight.Bold, 24.sp, lineHeight = 32.sp),
    bodyLarge = TextStyle(HeeboFamily, FontWeight.Normal, 16.sp, lineHeight = 24.sp),
    labelLarge = TextStyle(HeeboFamily, FontWeight.Bold, 14.sp),
)
