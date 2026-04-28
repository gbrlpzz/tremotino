import SwiftUI

private enum LibraryTab: String, CaseIterable, Identifiable {
    case prompts
    case profile
    case gold
    case bibliography
    case workflows
    case directories
    case design
    case stills
    case runbooks
    case registry

    var id: String { rawValue }

    var title: String {
        switch self {
        case .prompts: "Prompts"
        case .profile: "Profile"
        case .gold: "Gold"
        case .bibliography: "Bibliography"
        case .workflows: "Workflows"
        case .directories: "Directories"
        case .design: "Design"
        case .stills: "Stills"
        case .runbooks: "Runbooks"
        case .registry: "Registry"
        }
    }
}

struct LibraryView: View {
    @State private var selectedTab: LibraryTab = .prompts

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HeaderView(title: "Context", subtitle: "Prompts, profile, sources, workflows, and durable memory used by Tremotino agents.")

            HStack {
                Picker("Agent asset", selection: $selectedTab) {
                    ForEach(LibraryTab.allCases) { tab in
                        Text(tab.title).tag(tab)
                    }
                }
                .pickerStyle(.menu)
                .frame(width: 220)

                Spacer()
            }

            switch selectedTab {
            case .prompts:
                TypedDocumentsView(type: .prompt, showsHeader: false)
            case .profile:
                TypedDocumentsView(type: .profile, showsHeader: false)
            case .gold:
                TypedDocumentsView(type: .gold, showsHeader: false)
            case .bibliography:
                BibliographyView(showsHeader: false)
            case .workflows:
                TypedDocumentsView(type: .workflow, showsHeader: false)
            case .directories:
                TypedDocumentsView(type: .directory, showsHeader: false)
            case .design:
                TypedDocumentsView(type: .designMD, showsHeader: false)
            case .stills:
                StillsView(showsHeader: false)
            case .runbooks:
                RunbooksView(showsHeader: false)
            case .registry:
                RegistryView(showsHeader: false)
            }
        }
        .padding()
    }
}
