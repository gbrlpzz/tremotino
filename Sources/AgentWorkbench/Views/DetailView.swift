import SwiftUI

struct DetailView: View {
    @Environment(WorkbenchStore.self) private var store

    var body: some View {
        switch store.selection ?? .inbox {
        case .inbox:
            InboxView()
        case .workflows:
            TypedDocumentsView(type: .workflow)
        case .prompts:
            TypedDocumentsView(type: .prompt)
        case .profile:
            TypedDocumentsView(type: .profile)
        case .directories:
            TypedDocumentsView(type: .directory)
        case .skills:
            TypedDocumentsView(type: .skill)
        case .plugins:
            TypedDocumentsView(type: .plugin)
        case .design:
            TypedDocumentsView(type: .designMD)
        case .stills:
            StillsView()
        case .contextPacks:
            TypedDocumentsView(type: .contextPack)
        case .hay:
            TypedDocumentsView(type: .hay)
        case .jobs:
            JobsView()
        case .projects:
            ProjectsView()
        case .review:
            ReviewQueueView()
        case .runbooks:
            RunbooksView()
        case .gold:
            TypedDocumentsView(type: .gold)
        case .registry:
            RegistryView()
        case .settings:
            SettingsView()
        }
    }
}
