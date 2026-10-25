import Testing
@testable import VoiceAssistant

@Suite struct ThemeTests {
    @Test func lightTokens() {
        #expect(Theme.Palette.light.primary == 0x205FFF)
        #expect(Theme.Palette.light.background == 0xF5F6F7)
        #expect(Theme.Palette.light.surface == 0xFFFFFF)
        #expect(Theme.Palette.light.accent == 0xAA55FF)
    }

    @Test func darkTokens() {
        #expect(Theme.Palette.dark.primary == 0x205FFF)
        #expect(Theme.Palette.dark.link == 0x8CAAFF)
        #expect(Theme.Palette.dark.background == 0x0A0A0A)
        #expect(Theme.Palette.dark.surface == 0x1A1A1A)
        #expect(Theme.Palette.dark.accent == 0xC58BFF)
    }

    @Test func radii() {
        #expect(Theme.Radius.sheet == 20)
        #expect(Theme.Radius.card == 12)
    }
}
