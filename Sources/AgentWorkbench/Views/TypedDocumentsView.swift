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
    @State private var searchText = ""

    private var documents: [VaultDocument] {
        switch type {
        case .workflow: store.workflows
        case .prompt: store.prompts
        case .profile: store.profiles
        case .directory: store.directories
        case .bibliography: store.bibliographies
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

    private var visibleDocuments: [VaultDocument] {
        let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !query.isEmpty else { return documents }
        return documents.filter { document in
            document.title.lowercased().contains(query)
                || document.body.lowercased().contains(query)
                || document.path.path.lowercased().contains(query)
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
                DocumentSidebarList(documents: visibleDocuments, selectedID: $selectedID)
                .frame(minWidth: 240, maxWidth: 320)
                .onChange(of: selectedID) { _, newValue in
                    selectDocument(newValue)
                }
                .onAppear {
                    selectInitialDocumentIfNeeded()
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
        .searchable(text: $searchText, prompt: "Search \(sectionTitle.lowercased())")
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

    private func selectDocument(_ id: UUID?) {
        guard let id else {
            draft = nil
            return
        }
        let visibleMatch = visibleDocuments.first { document in document.id == id }
        let fullMatch = documents.first { document in document.id == id }
        draft = visibleMatch ?? fullMatch
    }

    private func selectInitialDocumentIfNeeded() {
        guard selectedID == nil else { return }
        let firstDocument = visibleDocuments.first
        selectedID = firstDocument?.id
        draft = firstDocument
    }

    private var sectionTitle: String {
        switch type {
        case .workflow: "Workflows"
        case .prompt: "Prompts and Style Guides"
        case .profile: "Operating Profile"
        case .directory: "Directories"
        case .bibliography: "Bibliography"
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

    fileprivate static func subtitle(for document: VaultDocument) -> String {
        if document.path.lastPathComponent == "SKILL.md" {
            let parent = document.path.deletingLastPathComponent().lastPathComponent
            if document.path.path.contains("/External/") {
                return "External skill / \(parent)"
            }
            if document.path.path.contains("/Packs/") {
                return "Pack skill / \(parent)"
            }
            return "Skill / \(parent)"
        }
        return document.path.lastPathComponent
    }

    private var sectionSubtitle: String {
        switch type {
        case .workflow: "Reusable agent workflows for Codex, Claude, and future clients."
        case .prompt: "System prompts, tone prompts, writing style guides, and client adapters."
        case .profile: "How you work, what you do, and collaboration defaults."
        case .directory: "Manual registry of important local folders and scan/edit policy."
        case .bibliography: "Source metadata, BibTeX entries, citation notes, DOI/URL checks, and report-ready reference context."
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

private struct DocumentSidebarList: View {
    let documents: [VaultDocument]
    @Binding var selectedID: UUID?

    var body: some View {
        List(documents, selection: $selectedID) { document in
            DocumentListRow(title: document.title, subtitle: TypedDocumentsView.subtitle(for: document))
                .tag(document.id)
        }
    }
}

private struct DocumentListRow: View {
    let title: String
    let subtitle: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .fontWeight(.medium)
                .lineLimit(1)
            Text(subtitle)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(1)
        }
    }
}
