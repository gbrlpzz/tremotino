import SwiftUI

struct TypedDocumentsView: View {
    @Environment(WorkbenchStore.self) private var store
    let type: VaultObjectType
    @State private var selectedID: UUID?
    @State private var draft: VaultDocument?

    private var documents: [VaultDocument] {
        switch type {
        case .workflow: store.workflows
        case .prompt: store.prompts
        case .profile: store.profiles
        case .directory: store.directories
        case .codexJob: []
        case .gold: store.goldItems
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HeaderView(title: sectionTitle, subtitle: sectionSubtitle)

            HStack(alignment: .top, spacing: 16) {
                List(documents, selection: $selectedID) { document in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(document.title)
                            .fontWeight(.medium)
                            .lineLimit(1)
                        Text(document.path.lastPathComponent)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                    }
                    .tag(document.id)
                }
                .frame(minWidth: 240, maxWidth: 320)
                .onChange(of: selectedID) { _, newValue in
                    draft = documents.first { $0.id == newValue }
                }
                .onAppear {
                    if selectedID == nil {
                        selectedID = documents.first?.id
                        draft = documents.first
                    }
                }

                if let binding = draftBinding {
                    VStack(alignment: .leading, spacing: 10) {
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
                    EmptyStateView(title: "No \(type.title.lowercased()) objects", detail: "Restart Tremotino to seed starter objects, or create one through an agent workflow.")
                }
            }

            FooterStatusView()
        }
        .padding()
    }

    private var draftBinding: Binding<VaultDocument>? {
        guard draft != nil else { return nil }
        return Binding(
            get: { draft! },
            set: { draft = $0 }
        )
    }

    private var sectionTitle: String {
        switch type {
        case .workflow: "Workflows"
        case .prompt: "Prompts and Style Guides"
        case .profile: "Operating Profile"
        case .directory: "Directories"
        case .codexJob: "Codex Jobs"
        case .gold: "Gold"
        }
    }

    private var sectionSubtitle: String {
        switch type {
        case .workflow: "Reusable agent workflows for Codex, Claude, and future clients."
        case .prompt: "System prompts, tone prompts, writing style guides, and client adapters."
        case .profile: "How you work, what you do, and collaboration defaults."
        case .directory: "Manual registry of important local folders and scan/edit policy."
        case .codexJob: "Queued and completed Codex CLI jobs."
        case .gold: "Refined reusable context spun from raw material."
        }
    }
}
