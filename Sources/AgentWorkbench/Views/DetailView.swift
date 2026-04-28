import SwiftUI

struct DetailView: View {
    @Environment(WorkbenchStore.self) private var store

    var body: some View {
        switch store.selection ?? .inbox {
        case .inbox:
            InboxView()
        case .projects:
            ProjectsView()
        case .review:
            ReviewQueueView()
        case .runbooks:
            RunbooksView()
        case .registry:
            RegistryView()
        case .settings:
            SettingsView()
        }
    }
}
