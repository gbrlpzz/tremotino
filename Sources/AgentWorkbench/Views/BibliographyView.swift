import SwiftUI
import UniformTypeIdentifiers

struct BibliographyView: View {
    @Environment(WorkbenchStore.self) private var store
    var showsHeader = true
    @State private var selectedID: UUID?
    @State private var draft: VaultDocument?
    @State private var showImporter = false

    private var bibTeXType: UTType {
        UTType(filenameExtension: "bib") ?? .plainText
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            if showsHeader {
                HeaderView(title: "Bibliography", subtitle: "BibTeX-backed reference memory for reports, papers, grants, and source-grounded agents.")
            }

            HStack {
                Button("New Reference") {
                    store.createDocument(type: .bibliography)
                }
                Button("Import BibTeX") {
                    showImporter = true
                }
                Button("Validate") {
                    store.validateBibliography()
                }
                Button("Review with Codex") {
                    store.createBibliographyReviewJob()
                }
                Spacer()
            }

            HStack(alignment: .top, spacing: 16) {
                List(store.bibliographies, selection: $selectedID) { document in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(document.title)
                            .fontWeight(.medium)
                            .lineLimit(2)
                        HStack(spacing: 8) {
                            Text(metadata("bibtex_key", in: document) ?? document.path.deletingPathExtension().lastPathComponent)
                            Text(metadata("year", in: document) ?? "No year")
                        }
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                    }
                    .tag(document.id)
                }
                .frame(minWidth: 280, maxWidth: 360)
                .onChange(of: selectedID) { _, newValue in
                    draft = store.bibliographies.first { $0.id == newValue }
                }
                .onAppear {
                    if selectedID == nil {
                        selectedID = store.bibliographies.first?.id
                        draft = store.bibliographies.first
                    }
                }

                if let binding = draftBinding {
                    VStack(alignment: .leading, spacing: 10) {
                        HStack(alignment: .firstTextBaseline) {
                            TextField("Title", text: binding.title)
                                .textFieldStyle(.roundedBorder)
                            Text(metadata("entry_type", in: binding.wrappedValue) ?? "reference")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }

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
                            Button("Send to Codex") {
                                store.createCodexJob(from: binding.wrappedValue)
                            }
                            Button("Save") {
                                store.saveDocument(binding.wrappedValue)
                            }
                            .keyboardShortcut(.defaultAction)
                        }
                    }
                } else {
                    EmptyStateView(title: "No bibliography entries", detail: "Import a .bib file or create a reference.")
                }
            }

            FooterStatusView()
        }
        .padding(showsHeader ? 16 : 0)
        .fileImporter(
            isPresented: $showImporter,
            allowedContentTypes: [bibTeXType, .plainText],
            allowsMultipleSelection: false
        ) { result in
            if case let .success(urls) = result, let url = urls.first {
                store.importBibTeX(from: url)
            }
        }
    }

    private var draftBinding: Binding<VaultDocument>? {
        guard draft != nil else { return nil }
        return Binding(
            get: { draft! },
            set: { draft = $0 }
        )
    }

    private func metadata(_ key: String, in document: VaultDocument) -> String? {
        document.body
            .split(separator: "\n")
            .first { line in
                line.trimmingCharacters(in: .whitespaces).hasPrefix("- \(key):")
            }?
            .description
            .replacingOccurrences(of: "- \(key):", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
