import SwiftUI
import UniformTypeIdentifiers

struct TypedDocumentsView: View {
    @Environment(WorkbenchStore.self) private var store
    let type: VaultObjectType
    var showsHeader = true
    @State private var selectedID: UUID?
    @State private var draft: VaultDocument?
    @State private var haySourcePaths = ""
    @State private var showHaySourcePicker = false

    private var documents: [VaultDocument] {
        switch type {
        case .workflow: store.workflows
        case .prompt: store.prompts
        case .profile: store.profiles
        case .directory: store.directories
        case .skill: store.skills
        case .plugin: store.plugins
        case .designMD: store.designs
        case .still: store.stills
        case .contextPack: store.contextPacks
        case .hay: store.hayItems
        case .codexJob: []
        case .gold: store.goldItems
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            if showsHeader {
                HeaderView(title: sectionTitle, subtitle: sectionSubtitle)
            }

            HStack {
                Button("New \(type.title)") {
                    store.createDocument(type: type)
                }
                if type == .contextPack, let draft {
                    Button("Assemble for Codex") {
                        store.statusMessage = store.assembleContextPack(draft, client: "codex").prefix(1200).description
                    }
                    Button("Assemble for Claude") {
                        store.statusMessage = store.assembleContextPack(draft, client: "claude").prefix(1200).description
                    }
                    Button("Queue Codex Job") {
                        store.createCodexJob(from: draft)
                    }
                } else if type == .hay, let draft {
                    Button("Choose Files or Folders") {
                        showHaySourcePicker = true
                    }
                    Button("Spin Hay with Codex") {
                        store.createHayIngestionJob(from: draft, sourcePaths: parsedHaySourcePaths)
                    }
                    .disabled(parsedHaySourcePaths.isEmpty)
                }
                Spacer()
            }

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

                        if type == .hay {
                            TextField("Files or folders to ingest", text: $haySourcePaths, prompt: Text("~/Downloads/raw, ~/Documents/source.pdf"))
                                .textFieldStyle(.roundedBorder)
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
                            Button("Spin into Gold") {
                                store.spinIntoGold(title: binding.wrappedValue.title, body: binding.wrappedValue.body, source: binding.wrappedValue.path.path)
                            }
                            Button("Send to Codex") {
                                if binding.wrappedValue.type == .hay {
                                    store.createHayIngestionJob(from: binding.wrappedValue, sourcePaths: parsedHaySourcePaths)
                                } else if binding.wrappedValue.type == .contextPack {
                                    store.createCodexJob(from: binding.wrappedValue)
                                } else {
                                    store.createCodexJob(from: binding.wrappedValue)
                                }
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
        .padding(showsHeader ? 16 : 0)
        .fileImporter(
            isPresented: $showHaySourcePicker,
            allowedContentTypes: [.item, .folder],
            allowsMultipleSelection: true
        ) { result in
            if case let .success(urls) = result {
                let picked = urls.map(\.path).joined(separator: "\n")
                haySourcePaths = [haySourcePaths, picked]
                    .filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
                    .joined(separator: "\n")
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

    private var parsedHaySourcePaths: [String] {
        haySourcePaths
            .split(whereSeparator: { $0 == "\n" || $0 == "," })
            .map { String($0).trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    }

    private var sectionTitle: String {
        switch type {
        case .workflow: "Workflows"
        case .prompt: "Prompts and Style Guides"
        case .profile: "Operating Profile"
        case .directory: "Directories"
        case .skill: "Skills"
        case .plugin: "Plugin Packs"
        case .designMD: "Design Systems"
        case .still: "Stills"
        case .contextPack: "Context Packs"
        case .hay: "Hay"
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
        case .skill: "Portable agent capabilities with trigger conditions and bounded instructions."
        case .plugin: "Curated local packs of approved Markdown assets. No executable plugin code in this phase."
        case .designMD: "Agent-readable DESIGN.md files and visual system guidance."
        case .still: "Local visual references with Markdown sidecars and explicit usage notes."
        case .contextPack: "Bundles of profile, prompts, workflows, design, stills, directories, and gold context for agents."
        case .hay: "Disordered raw material queued for Codex extraction into durable Gold and typed assets."
        case .codexJob: "Queued and completed Codex CLI jobs."
        case .gold: "Refined reusable context spun from raw material."
        }
    }
}
