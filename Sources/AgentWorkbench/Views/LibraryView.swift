import SwiftUI

private enum LibraryTab: String, CaseIterable, Identifiable {
    case bibliography
    case gold
    case skills
    case prompts
    case workflows
    case profile
    case directories
    case design
    case stills
    case plugins
    case runbooks
    case registry

    var id: String { rawValue }

    var title: String {
        switch self {
        case .bibliography: "Bibliography"
        case .gold: "Gold"
        case .skills: "Skills"
        case .prompts: "Prompts"
        case .workflows: "Workflows"
        case .profile: "Profile"
        case .directories: "Directories"
        case .design: "Design"
        case .stills: "Stills"
        case .plugins: "Plugins"
        case .runbooks: "Runbooks"
        case .registry: "Registry"
        }
    }
}

struct LibraryView: View {
    @State private var selectedTab: LibraryTab = .bibliography

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HeaderView(title: "Agent Hub", subtitle: "Cross-agent MCP memory, skills, prompts, files, and design assets for Codex and Claude.")

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
            case .bibliography:
                BibliographyView(showsHeader: false)
            case .gold:
                TypedDocumentsView(type: .gold, showsHeader: false)
            case .skills:
                TypedDocumentsView(type: .skill, showsHeader: false)
            case .prompts:
                TypedDocumentsView(type: .prompt, showsHeader: false)
            case .workflows:
                TypedDocumentsView(type: .workflow, showsHeader: false)
            case .profile:
                TypedDocumentsView(type: .profile, showsHeader: false)
            case .directories:
                TypedDocumentsView(type: .directory, showsHeader: false)
            case .design:
                TypedDocumentsView(type: .designMD, showsHeader: false)
            case .stills:
                StillsView(showsHeader: false)
            case .plugins:
                TypedDocumentsView(type: .plugin, showsHeader: false)
            case .runbooks:
                RunbooksView(showsHeader: false)
            case .registry:
                RegistryView(showsHeader: false)
            }
        }
        .padding()
    }
}
