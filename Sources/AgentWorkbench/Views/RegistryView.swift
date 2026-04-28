import SwiftUI

struct RegistryView: View {
    @Environment(WorkbenchStore.self) private var store
    var showsHeader = true

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            if showsHeader {
                HeaderView(title: "MCP Registry", subtitle: "Monitor protocol and registry updates without auto-installing servers.")
            }

            Button {
                Task { await store.refreshRegistry() }
            } label: {
                Label("Refresh Registry Monitor", systemImage: "arrow.clockwise")
            }

            if store.registrySnapshots.isEmpty {
                EmptyStateView(title: "No registry snapshot", detail: "Refresh to fetch registry, spec, and roadmap status.")
            } else {
                List(store.registrySnapshots, id: \.self) { snapshot in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(snapshot.title)
                                .fontWeight(.semibold)
                            Spacer()
                            Text(snapshot.status)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        Text(snapshot.detail)
                            .foregroundStyle(.secondary)
                        if let fetchedAt = snapshot.fetchedAt {
                            Text(fetchedAt.formatted(date: .abbreviated, time: .standard))
                                .font(.caption)
                                .foregroundStyle(.tertiary)
                        }
                    }
                    .padding(.vertical, 5)
                }
            }

            FooterStatusView()
        }
        .padding(showsHeader ? 16 : 0)
    }
}
