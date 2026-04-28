import SwiftUI

struct HeaderView: View {
    var title: String
    var subtitle: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.largeTitle)
                .fontWeight(.semibold)
            Text(subtitle)
                .foregroundStyle(.secondary)
        }
    }
}

struct EmptyStateView: View {
    var title: String
    var detail: String

    var body: some View {
        ContentUnavailableView(title, systemImage: "tray", description: Text(detail))
            .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

struct FooterStatusView: View {
    @Environment(WorkbenchStore.self) private var store

    var body: some View {
        HStack {
            Text(store.statusMessage)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(1)
            Spacer()
            Text("\(store.indexCount) indexed")
                .font(.caption)
                .foregroundStyle(.tertiary)
        }
    }
}
