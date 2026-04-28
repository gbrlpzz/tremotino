import SwiftUI

struct RunbooksView: View {
    @Environment(WorkbenchStore.self) private var store

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HeaderView(title: "Runbooks", subtitle: "Safe workflow actions exposed as reviewable buttons and MCP dry runs.")

            List(store.runbooks) { runbook in
                VStack(alignment: .leading, spacing: 6) {
                    Text(runbook.title)
                        .fontWeight(.semibold)
                    Text(runbook.detail)
                        .foregroundStyle(.secondary)
                    Text(runbook.commandPreview)
                        .font(.system(.caption, design: .monospaced))
                        .foregroundStyle(.tertiary)

                    if runbook.id == "rebuild-index" {
                        Button("Run") {
                            Task { await store.rebuildIndex() }
                        }
                    } else if runbook.id == "scan-projects" {
                        Button("Run") {
                            store.scanKnownProjects()
                        }
                    } else if runbook.id == "registry-refresh" {
                        Button("Run") {
                            Task { await store.refreshRegistry() }
                        }
                    }
                }
                .padding(.vertical, 6)
            }

            FooterStatusView()
        }
        .padding()
    }
}
