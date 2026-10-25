import SwiftUI

public struct RootView: View {
    public init() {}
    public var body: some View {
        Text("Voice Assistant")
            .font(Theme.Font.title)
            .foregroundStyle(Theme.Colors.ink)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Theme.Colors.background)
    }
}

// Add `@main` in the Xcode app target that wraps this library:
// @main struct VoiceAssistantApp: App { var body: some Scene { WindowGroup { RootView() } } }
