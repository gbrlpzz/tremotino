import SwiftUI

struct ReviewQueueView: View {
    @Environment(WorkbenchStore.self) private var store

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HeaderView(title: "Review Queue", subtitle: "Agent-written updates wait here before becoming durable memory.")

            if store.proposals.isEmpty {
                EmptyStateView(title: "No proposals", detail: "Project scans and MCP propose tools will add pending items here.")
            } else {
                List(store.proposals) { proposal in
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text(proposal.title)
                                .fontWeight(.semibold)
                            Spacer()
                            Text(proposal.status.rawValue.capitalized)
                                .font(.caption)
                                .foregroundStyle(proposal.status == .pending ? .orange : .secondary)
                        }

                        Text(proposal.body)
                            .foregroundStyle(.secondary)
                            .lineLimit(5)

                        HStack {
                            Text(proposal.source)
                                .font(.caption)
                                .foregroundStyle(.tertiary)
                            Spacer()
                            Button("Reject") {
                                store.reject(proposal)
                            }
                            .disabled(proposal.status != .pending)
                            Button("Approve") {
                                store.approve(proposal)
                            }
                            .disabled(proposal.status != .pending)
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
