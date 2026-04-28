import AppKit
import SwiftUI

private enum LibraryFilter: String, CaseIterable, Identifiable {
    case all
    case skills
    case prompts
    case workflows
    case profile
    case design
    case bibliography
    case gold
    case stills
    case packs
    case contextPacks

    var id: String { rawValue }

    var title: String {
        switch self {
        case .all: "All"
        case .skills: "Skills"
        case .prompts: "Prompts"
        case .workflows: "Workflows"
        case .profile: "Profile"
        case .design: "Design"
        case .bibliography: "Bibliography"
        case .gold: "Gold"
        case .stills: "Stills"
        case .packs: "Packs"
        case .contextPacks: "Context Packs"
        }
    }

    func includes(_ type: VaultObjectType) -> Bool {
        switch self {
        case .all: true
        case .skills: type == .skill
        case .prompts: type == .prompt
        case .workflows: type == .workflow
        case .profile: type == .profile
        case .design: type == .designMD
        case .bibliography: type == .bibliography
        case .gold: type == .gold
        case .stills: type == .still
        case .packs: type == .plugin
        case .contextPacks: type == .contextPack
        }
    }
}

struct LibraryView: View {
    @Environment(WorkbenchStore.self) private var store
    @State private var filter: LibraryFilter = .all
    @State private var query = ""
    @State private var selectedID: UUID?
    @State private var draft: VaultDocument?

    private var visibleDocuments: [VaultDocument] {
        let normalizedQuery = query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        return store.libraryDocuments.filter { document in
            filter.includes(document.type)
                && (normalizedQuery.isEmpty
                    || document.title.lowercased().contains(normalizedQuery)
                    || document.body.lowercased().contains(normalizedQuery)
                    || document.path.path.lowercased().contains(normalizedQuery))
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HeaderView(
                title: "Agent Library",
                subtitle: "The portable context and skill layer shared by Codex, Claude, and future agents."
            )

            HStack(spacing: 10) {
                Picker("Filter", selection: $filter) {
                    ForEach(LibraryFilter.allCases) { filter in
                        Text(filter.title).tag(filter)
                    }
                }
                .pickerStyle(.menu)
                .frame(width: 190)

                TextField("Search library", text: $query)
                    .textFieldStyle(.roundedBorder)
                    .frame(maxWidth: 380)

                Text("\(visibleDocuments.count) shown")
                    .foregroundStyle(.secondary)

                Spacer()

                Button("New Skill") {
                    store.createDocument(type: .skill)
                }
                Button("New Prompt") {
                    store.createDocument(type: .prompt)
                }
            }

            HStack(alignment: .top, spacing: 16) {
                List(visibleDocuments, selection: $selectedID) { document in
                    LibraryRow(document: document)
                        .tag(document.id)
                }
                .frame(minWidth: 300, idealWidth: 360, maxWidth: 460)
                .onAppear {
                    selectFirstIfNeeded()
                }
                .onChange(of: selectedID) { _, newValue in
                    selectDocument(newValue)
                }
                .onChange(of: filter) { _, _ in
                    selectFirstVisible()
                }
                .onChange(of: query) { _, _ in
                    if let selectedID, visibleDocuments.contains(where: { $0.id == selectedID }) {
                        selectDocument(selectedID)
                    } else {
                        selectFirstVisible()
                    }
                }

                if let binding = draftBinding {
                    LibraryDetail(document: binding)
                } else {
                    EmptyStateView(
                        title: "No library item selected",
                        detail: "Choose an item from the Agent Library or create a new skill or prompt."
                    )
                }
            }

            FooterStatusView()
        }
        .padding()
    }

    private var draftBinding: Binding<VaultDocument>? {
        guard draft != nil else { return nil }
        return Binding(get: { draft! }, set: { draft = $0 })
    }

    private func selectFirstIfNeeded() {
        guard selectedID == nil else { return }
        selectFirstVisible()
    }

    private func selectFirstVisible() {
        let first = visibleDocuments.first
        selectedID = first?.id
        draft = first
    }

    private func selectDocument(_ id: UUID?) {
        guard let id else {
            draft = nil
            return
        }
        draft = visibleDocuments.first { $0.id == id } ?? store.libraryDocuments.first { $0.id == id }
    }
}

private struct LibraryRow: View {
    let document: VaultDocument

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(document.title)
                    .fontWeight(.medium)
                    .lineLimit(1)
                Spacer()
                Text(document.type.title)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }

            Text(subtitle)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(2)
        }
        .padding(.vertical, 4)
    }

    private var subtitle: String {
        if document.path.lastPathComponent == "SKILL.md" {
            return "Skill / \(document.path.deletingLastPathComponent().lastPathComponent)"
        }
        return document.path.lastPathComponent
    }
}

private struct LibraryDetail: View {
    @Environment(WorkbenchStore.self) private var store
    @Binding var document: VaultDocument

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(document.type.title)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    TextField("Title", text: $document.title)
                        .font(.title2.weight(.semibold))
                        .textFieldStyle(.plain)
                }

                Spacer()

                Button("Reveal") {
                    NSWorkspace.shared.activateFileViewerSelecting([document.path])
                }
                Button("Send to Codex") {
                    store.createCodexJob(from: document)
                }
                Button("Save") {
                    store.saveDocument(document)
                }
                .keyboardShortcut(.defaultAction)
            }

            HStack {
                Text(document.path.path)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                    .textSelection(.enabled)
                Spacer()
                if let status = document.status, !status.isEmpty {
                    Text(status.capitalized)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            TextEditor(text: $document.body)
                .font(.body)
                .scrollContentBackground(.hidden)
                .background(.quaternary.opacity(0.45))
                .clipShape(RoundedRectangle(cornerRadius: 8))
        }
    }
}
