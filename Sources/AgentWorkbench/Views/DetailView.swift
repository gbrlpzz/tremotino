import SwiftUI

struct DetailView: View {
    @Environment(WorkbenchStore.self) private var store

    var body: some View {
        switch store.selection ?? .capture {
        case .capture:
            InboxView()
        case .spin:
            SpinView()
        case .review:
            ReviewQueueView()
        case .library:
            LibraryView()
        case .settings:
            SettingsView()
        }
    }
}
