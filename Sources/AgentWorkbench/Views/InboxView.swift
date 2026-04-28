import SwiftUI

struct InboxView: View {
    @Environment(WorkbenchStore.self) private var store

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HeaderView(title: "Inbox", subtitle: "Fast capture before filing into durable memory.")

            if store.inboxNotes.isEmpty {
                EmptyStateView(title: "No captures yet", detail: "Use Quick Capture or Cmd-Shift-N to add the first note.")
            } else {
                List(store.inboxNotes) { note in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(note.title)
                            .fontWeight(.medium)
                        Text(note.body)
                            .foregroundStyle(.secondary)
                            .lineLimit(3)
                        Text(note.path.path)
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                            .lineLimit(1)
                        HStack {
                            Button("Send to Codex") {
                                store.createCodexJob(from: note)
                            }
                            Button("Spin into Gold") {
                                store.spinIntoGold(title: note.title, body: note.body, source: note.path.path)
                            }
                        }
                    }
                    .padding(.vertical, 4)
                }
            }

            FooterStatusView()
        }
        .padding()
    }
}
