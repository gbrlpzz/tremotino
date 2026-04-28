import AppKit
import SwiftUI

struct SkillsView: View {
    @Environment(WorkbenchStore.self) private var store
    @State private var selectedID: UUID?
    @State private var draft: VaultDocument?
    @State private var searchText = ""

    private var visibleSkills: [VaultDocument] {
        let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !query.isEmpty else { return store.skills }
        return store.skills.filter { skill in
            skill.title.lowercased().contains(query)
                || skill.body.lowercased().contains(query)
                || skill.path.path.lowercased().contains(query)
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HeaderView(
                title: "Skills",
                subtitle: "One installed skill library for Codex, Claude, and future agents. Cloned and local skills are shown together."
            )

            HStack(spacing: 10) {
                TextField("Search installed skills", text: $searchText)
                    .textFieldStyle(.roundedBorder)
                    .frame(maxWidth: 360)

                Text("\(store.skills.count) installed")
                    .foregroundStyle(.secondary)

                Spacer()

                Button("New Skill") {
                    store.createDocument(type: .skill)
                }
                Button("Reload") {
                    do {
                        try store.refresh()
                        selectInitialSkillIfNeeded()
                    } catch {
                        store.statusMessage = "Reload failed: \(error.localizedDescription)"
                    }
                }
            }

            HStack(alignment: .top, spacing: 16) {
                List(visibleSkills, selection: $selectedID) { skill in
                    SkillRow(skill: skill)
                        .tag(skill.id)
                }
                .frame(minWidth: 280, idealWidth: 340, maxWidth: 420)
                .onChange(of: selectedID) { _, newValue in
                    selectSkill(newValue)
                }
                .onChange(of: searchText) { _, _ in
                    if let selectedID, visibleSkills.contains(where: { $0.id == selectedID }) {
                        selectSkill(selectedID)
                    } else {
                        selectFirstVisibleSkill()
                    }
                }
                .onAppear {
                    selectInitialSkillIfNeeded()
                }

                if let binding = draftBinding {
                    SkillDetail(skill: binding)
                } else {
                    EmptyStateView(
                        title: "No skills installed",
                        detail: "Install a curated pack or create a skill to make it available to Tremotino agents."
                    )
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

    private func selectSkill(_ id: UUID?) {
        guard let id else {
            draft = nil
            return
        }
        draft = visibleSkills.first { $0.id == id } ?? store.skills.first { $0.id == id }
    }

    private func selectInitialSkillIfNeeded() {
        guard selectedID == nil else { return }
        selectFirstVisibleSkill()
    }

    private func selectFirstVisibleSkill() {
        let first = visibleSkills.first
        selectedID = first?.id
        draft = first
    }
}

private struct SkillRow: View {
    let skill: VaultDocument

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(skill.title)
                .fontWeight(.medium)
                .lineLimit(1)

            Text(SkillMetadata.summary(for: skill))
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(2)
        }
        .padding(.vertical, 4)
    }
}

private struct SkillDetail: View {
    @Environment(WorkbenchStore.self) private var store
    @Binding var skill: VaultDocument

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(skill.title)
                        .font(.title2)
                        .fontWeight(.semibold)
                        .lineLimit(2)

                    Text(SkillMetadata.origin(for: skill))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }

                Spacer()

                Button("Reveal") {
                    NSWorkspace.shared.activateFileViewerSelecting([skill.path])
                }
                Button("Send to Codex") {
                    store.createCodexJob(from: skill)
                }
                Button("Save") {
                    store.saveDocument(skill)
                }
                .keyboardShortcut(.defaultAction)
            }

            Text(skill.path.path)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(1)
                .textSelection(.enabled)

            TextEditor(text: $skill.body)
                .font(.body)
                .scrollContentBackground(.hidden)
                .background(.quaternary.opacity(0.45))
                .clipShape(RoundedRectangle(cornerRadius: 8))
        }
    }
}

private enum SkillMetadata {
    static func summary(for skill: VaultDocument) -> String {
        if let description = frontmatterValue("description", in: skill.body), !description.isEmpty {
            return clean(description)
        }
        let body = skill.body
            .replacingOccurrences(of: "\n", with: " ")
            .replacingOccurrences(of: "#", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        return String(body.prefix(150))
    }

    static func origin(for skill: VaultDocument) -> String {
        let components = skill.path.pathComponents
        if let externalIndex = components.firstIndex(of: "External"), components.indices.contains(externalIndex + 2) {
            return "Copied from ~/.\(components[externalIndex + 1])/skills"
        }
        if let packIndex = components.firstIndex(of: "Packs"), components.indices.contains(packIndex + 1) {
            return "Installed from \(components[packIndex + 1])"
        }
        return "Local Tremotino skill"
    }

    private static func frontmatterValue(_ key: String, in content: String) -> String? {
        for line in content.split(separator: "\n") {
            let trimmed = String(line).trimmingCharacters(in: .whitespaces)
            if trimmed.hasPrefix("\(key):") {
                return trimmed
                    .replacingOccurrences(of: "\(key):", with: "")
                    .trimmingCharacters(in: .whitespacesAndNewlines)
                    .trimmingCharacters(in: CharacterSet(charactersIn: "\"'"))
            }
        }
        return nil
    }

    private static func clean(_ value: String) -> String {
        value
            .replacingOccurrences(of: ">", with: "")
            .replacingOccurrences(of: "\"", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
