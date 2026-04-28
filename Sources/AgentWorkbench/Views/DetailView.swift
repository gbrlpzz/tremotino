import SwiftUI

struct DetailView: View {
    @Environment(WorkbenchStore.self) private var store

    var body: some View {
        switch store.selection ?? .skills {
        case .capture:
            InboxView()
        case .spin:
            SpinView()
        case .skills:
            SkillsView()
        case .context:
            LibraryView()
        case .review:
            ReviewQueueView()
        case .settings:
            SettingsView()
        }
    }
}
