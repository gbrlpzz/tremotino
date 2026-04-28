import SwiftUI

struct ProjectsView: View {
    @Environment(WorkbenchStore.self) private var store

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HeaderView(title: "Projects", subtitle: "Workflow-centered memory for active work.")

            HStack {
                Button {
                    store.scanKnownProjects()
                } label: {
                    Label("Scan Known Projects", systemImage: "doc.text.magnifyingglass")
                }

                Text("Scanning is read-only and creates review proposals.")
                    .foregroundStyle(.secondary)
            }

            List(store.projects) { project in
                VStack(alignment: .leading, spacing: 5) {
                    HStack {
                        Text(project.title)
                            .fontWeight(.semibold)
                        Text(project.kind.label)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Text(project.summary)
                        .foregroundStyle(.secondary)
                    Text(project.path)
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                }
                .padding(.vertical, 5)
            }

            FooterStatusView()
        }
        .padding()
    }
}
