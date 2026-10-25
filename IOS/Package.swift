// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "VoiceAssistant",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [.library(name: "VoiceAssistant", targets: ["VoiceAssistant"])],
    targets: [
        .target(name: "VoiceAssistant", path: "VoiceAssistant", exclude: ["Resources"]),
        .testTarget(name: "VoiceAssistantTests", dependencies: ["VoiceAssistant"], path: "VoiceAssistantTests"),
    ],
    swiftLanguageModes: [.v6]
)
