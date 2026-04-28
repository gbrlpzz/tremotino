import SwiftUI

private enum SpinTab: String, CaseIterable, Identifiable {
    case hay
    case contextPacks
    case jobs
    case projects

    var id: String { rawValue }

    var title: String {
        switch self {
        case .hay: "Inputs"
        case .contextPacks: "Context"
        case .jobs: "Jobs"
        case .projects: "Projects"
        }
    }
}

struct SpinView: View {
    @State private var selectedTab: SpinTab = .hay

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HeaderView(title: "Hay to Gold", subtitle: "Compact messy folders and files into reviewable long-term memory.")

            Picker("Spin section", selection: $selectedTab) {
                ForEach(SpinTab.allCases) { tab in
                    Text(tab.title).tag(tab)
                }
            }
            .pickerStyle(.segmented)

            switch selectedTab {
            case .hay:
                TypedDocumentsView(type: .hay, showsHeader: false)
            case .contextPacks:
                TypedDocumentsView(type: .contextPack, showsHeader: false)
            case .jobs:
                JobsView(showsHeader: false)
            case .projects:
                ProjectsView(showsHeader: false)
            }
        }
        .padding()
    }
}
