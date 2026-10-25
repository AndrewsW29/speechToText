import SwiftUI

// Heebo: bundle Heebo-*.ttf and list in UIAppFonts. Until then text falls back to the system font;
// Font.custom(_, relativeTo:) keeps Dynamic Type scaling once registered.
public enum Theme {
    public struct Palette: Sendable {
        public let primary: UInt32
        public let link: UInt32
        public let background: UInt32
        public let surface: UInt32
        public let ink: UInt32
        public let muted: UInt32
        public let accent: UInt32

        public static let light = Palette(
            primary: 0x205FFF, link: 0x205FFF, background: 0xF5F6F7, surface: 0xFFFFFF,
            ink: 0x0A0A0A, muted: 0x5C6B80, accent: 0xAA55FF)
        public static let dark = Palette(
            primary: 0x205FFF, link: 0x8CAAFF, background: 0x0A0A0A, surface: 0x1A1A1A,
            ink: 0xF5F6F7, muted: 0x9CA3AF, accent: 0xC58BFF)
    }

    public enum Radius {
        public static let card: CGFloat = 12
        public static let sheet: CGFloat = 20
    }

    public enum Colors {
        public static let primary = dynamic(\.primary)
        public static let background = dynamic(\.background)
        public static let surface = dynamic(\.surface)
        public static let ink = dynamic(\.ink)
        public static let muted = dynamic(\.muted)
        public static let accent = dynamic(\.accent)

        private static func dynamic(_ key: KeyPath<Palette, UInt32>) -> Color {
            #if canImport(UIKit)
            return Color(UIColor { $0.userInterfaceStyle == .dark
                ? UIColor(hex: Palette.dark[keyPath: key]) : UIColor(hex: Palette.light[keyPath: key]) })
            #else
            return Color(hex: Palette.light[keyPath: key])
            #endif
        }
    }

    public enum Font {
        public static let title = SwiftUI.Font.custom("Heebo-ExtraBold", size: 34, relativeTo: .largeTitle)
        public static let body = SwiftUI.Font.custom("Heebo-Regular", size: 16, relativeTo: .body)
        public static let label = SwiftUI.Font.custom("Heebo-Bold", size: 14, relativeTo: .subheadline)
    }
}

extension Color {
    init(hex: UInt32) {
        self.init(red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255)
    }
}

#if canImport(UIKit)
import UIKit
extension UIColor {
    convenience init(hex: UInt32) {
        self.init(red: CGFloat((hex >> 16) & 0xFF) / 255, green: CGFloat((hex >> 8) & 0xFF) / 255,
                  blue: CGFloat(hex & 0xFF) / 255, alpha: 1)
    }
}
#endif
