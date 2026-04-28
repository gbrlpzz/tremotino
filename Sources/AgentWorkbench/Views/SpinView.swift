import SwiftUI

private enum SpinTab: String, CaseIterable, Identifiable {
    case inbox
    case hay
    case jobs
    case gold

    var id: String { rawValue }

    var title: String {
        switch self {
        case .inbox: "Inbox"
        case .hay: "Inputs"
        case .jobs: "Jobs"
        case .gold: "Gold"
        }
    }
}

struct SpinView: View {
    @State private var selectedTab: SpinTab = .inbox

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
            case .inbox:
                InboxView(showsHeader: false)
            case .hay:
                TypedDocumentsView(type: .hay, showsHeader: false)
            case .jobs:
                JobsView(showsHeader: false)
            case .gold:
                TypedDocumentsView(type: .gold, showsHeader: false)
            }
        }
        .padding()
    }
}
