import SwiftUI

struct JobsView: View {
    @Environment(WorkbenchStore.self) private var store

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HeaderView(title: "Codex Jobs", subtitle: "Queued scoped Codex CLI work. Jobs require a manual Run click.")

            if store.codexJobs.isEmpty {
                EmptyStateView(title: "No jobs queued", detail: "Use Send to Codex from Workflows, Prompts, Profile, Inbox, or Gold.")
            } else {
                List(store.codexJobs) { job in
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text(job.title)
                                .fontWeight(.semibold)
                            Spacer()
                            Text(job.status.capitalized)
                                .font(.caption)
                                .foregroundStyle(job.status == "queued" ? .orange : .secondary)
                        }

                        Text("Workflow: \(job.workflow)")
                            .foregroundStyle(.secondary)
                        Text("Working directory: \(job.workingDirectory)")
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                            .lineLimit(1)
                        Text("Writable: \(job.writablePaths.joined(separator: ", "))")
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                            .lineLimit(1)

                        HStack {
                            Text(job.path.deletingLastPathComponent().path)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .lineLimit(1)
                            Spacer()
                            Button("Run") {
                                store.runCodexJob(job)
                            }
                            .disabled(job.status == "running")
                        }
                    }
                    .padding(.vertical, 6)
                }
            }

            FooterStatusView()
        }
        .padding()
    }
}
