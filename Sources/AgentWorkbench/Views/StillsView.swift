import SwiftUI
import AppKit

struct StillsView: View {
    @Environment(WorkbenchStore.self) private var store
    var showsHeader = true
    @State private var selectedID: UUID?
    @State private var draft: VaultDocument?

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            if showsHeader {
                HeaderView(title: "Stills", subtitle: "Local visual references stored as media files plus Markdown sidecars.")
            }

            HStack {
                Button("New Still") {
                    store.createDocument(type: .still)
                }
                Spacer()
            }

            HStack(alignment: .top, spacing: 16) {
                List(store.stills, selection: $selectedID) { still in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(still.title)
                            .fontWeight(.medium)
                            .lineLimit(1)
                        Text(mediaPath(in: still) ?? still.path.lastPathComponent)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                    }
                    .tag(still.id)
                }
                .frame(minWidth: 240, maxWidth: 320)
                .onChange(of: selectedID) { _, newValue in
                    draft = store.stills.first { $0.id == newValue }
                }
                .onAppear {
                    if selectedID == nil {
                        selectedID = store.stills.first?.id
                        draft = store.stills.first
                    }
                }

                if let binding = draftBinding {
                    VStack(alignment: .leading, spacing: 10) {
                        stillPreview(for: binding.wrappedValue)
                            .frame(maxWidth: .infinity, minHeight: 180, maxHeight: 280)
                            .background(.quaternary.opacity(0.35))
                            .clipShape(RoundedRectangle(cornerRadius: 8))

                        TextField("Title", text: binding.title)
                            .textFieldStyle(.roundedBorder)

                        TextEditor(text: binding.body)
                            .font(.body)
                            .scrollContentBackground(.hidden)
                            .background(.quaternary.opacity(0.45))
                            .clipShape(RoundedRectangle(cornerRadius: 8))

                        HStack {
                            Text(binding.wrappedValue.path.path)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .lineLimit(1)
                            Spacer()
                            Button("Spin into Gold") {
                                store.spinIntoGold(title: binding.wrappedValue.title, body: binding.wrappedValue.body, source: binding.wrappedValue.path.path)
                            }
                            Button("Send Reference to Codex") {
                                store.createCodexJob(from: binding.wrappedValue)
                            }
                            Button("Save") {
                                store.saveDocument(binding.wrappedValue)
                            }
                            .keyboardShortcut(.defaultAction)
                        }
                    }
                } else {
                    EmptyStateView(title: "No stills", detail: "Create a still sidecar, then place private media in Stills/Files.")
                }
            }

            FooterStatusView()
        }
        .padding(showsHeader ? 16 : 0)
    }

    private var draftBinding: Binding<VaultDocument>? {
        guard draft != nil else { return nil }
        return Binding(
            get: { draft! },
            set: { draft = $0 }
        )
    }

    @ViewBuilder
    private func stillPreview(for document: VaultDocument) -> some View {
        if let url = resolvedMediaURL(for: document), let image = NSImage(contentsOf: url) {
            Image(nsImage: image)
                .resizable()
                .scaledToFit()
                .padding(8)
        } else {
            VStack(spacing: 8) {
                Image(systemName: "photo.on.rectangle")
                    .font(.largeTitle)
                    .foregroundStyle(.secondary)
                Text(mediaPath(in: document) ?? "No media_path set")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }

    private func resolvedMediaURL(for document: VaultDocument) -> URL? {
        guard let rawPath = mediaPath(in: document), !rawPath.isEmpty else { return nil }
        let expanded = NSString(string: rawPath).expandingTildeInPath
        if expanded.hasPrefix("/") {
            return URL(fileURLWithPath: expanded)
        }
        return store.paths.stills.appendingPathComponent(rawPath)
    }

    private func mediaPath(in document: VaultDocument) -> String? {
        document.body
            .split(separator: "\n")
            .first { $0.trimmingCharacters(in: .whitespaces).hasPrefix("media_path:") }?
            .split(separator: ":", maxSplits: 1)
            .last?
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
