Heebo: Type.kt uses the Google Fonts downloadable provider (needs res/values/font_certs.xml
from the Android Studio "Downloadable Fonts" wizard). To bundle instead, drop heebo_regular.ttf,
heebo_medium.ttf, heebo_bold.ttf, heebo_extrabold.ttf here and swap Type.kt to Font(R.font.*).
