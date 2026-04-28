import Foundation

struct MarkdownStore {
    var paths: WorkbenchPaths
    private let fileManager = FileManager.default

    func bootstrapVault() throws {
        for directory in [
            paths.vaultRoot,
            paths.inbox,
            paths.projects,
            paths.review,
            paths.runbooks,
            paths.supportRoot
        ] {
            try fileManager.createDirectory(at: directory, withIntermediateDirectories: true)
        }

        try writeSeedIfNeeded(
            at: paths.vaultRoot.appendingPathComponent("README.md"),
            title: "Tremotino Vault",
            type: "system",
            body: """
            # Tremotino Vault

            This folder is the Markdown-first source of truth for Tremotino.

            Generated indexes live outside this vault and can be rebuilt.
            Agents should propose durable updates into the review queue before they become memory.
            """
        )

        try writeSeedIfNeeded(
            at: paths.projects.appendingPathComponent("research-moat-hub.md"),
            title: "Research Moat Hub",
            type: "research_moat",
            body: """
            # Research Moat Hub

            This is the durable map of sources, claims, projects, institutions, people, applications, and reusable arguments.

            ## Observations
            - [principle] The vault should preserve provenance and uncertainty, not flatten research into generic notes.
            - [principle] Agent-written updates enter the review queue before becoming durable memory.
            - [principle] Reusable arguments should link back to source material, project evidence, and prior drafts.

            ## Relations
            - relates_to [[Projects]]
            - relates_to [[Review Queue]]
            - supports [[Grant & Applications]]
            - supports [[Research Packs]]
            """
        )

        try writeSeedIfNeeded(
            at: paths.runbooks.appendingPathComponent("rebuild-index.md"),
            title: "Rebuild Index",
            type: "runbook",
            body: """
            # Rebuild Index

            Dry-run command:

            ```sh
            tremotino rebuild-index
            ```

            Rebuilds the disposable search index from Markdown files in the vault.
            """
        )
    }

    func createInboxNote(title: String, body: String, tags: [String]) throws {
        let slug = slugify(title.isEmpty ? "capture" : title)
        let filename = "\(timestampSlug())-\(slug).md"
        let url = paths.inbox.appendingPathComponent(filename)
        let content = markdown(title: title.isEmpty ? "Untitled Capture" : title, type: "inbox", tags: tags, body: body)
        try content.write(to: url, atomically: true, encoding: .utf8)
    }

    func createProposal(title: String, body: String, source: String) throws {
        let filename = "\(timestampSlug())-\(slugify(title)).md"
        let url = paths.review.appendingPathComponent(filename)
        let content = """
        ---
        title: \(escapeYaml(title))
        type: proposal
        status: pending
        source: \(escapeYaml(source))
        created_at: \(ISO8601DateFormatter().string(from: Date()))
        ---

        # \(title)

        \(body)
        """
        try content.write(to: url, atomically: true, encoding: .utf8)
    }

    func approveProposal(_ proposal: ReviewProposal) throws {
        let title = proposal.title.replacingOccurrences(of: "Proposal: ", with: "")
        let filename = "\(timestampSlug())-\(slugify(title)).md"
        let destination = paths.projects.appendingPathComponent(filename)
        let content = markdown(title: title, type: "memory", tags: ["approved"], body: proposal.body)
        try content.write(to: destination, atomically: true, encoding: .utf8)
        try markProposal(proposal, status: .approved)
    }

    func rejectProposal(_ proposal: ReviewProposal) throws {
        try markProposal(proposal, status: .rejected)
    }

    func listInboxNotes() throws -> [WorkbenchNote] {
        try listMarkdown(in: paths.inbox).map(note(from:))
            .sorted { $0.createdAt > $1.createdAt }
    }

    func listReviewProposals() throws -> [ReviewProposal] {
        try listMarkdown(in: paths.review).map(proposal(from:))
            .sorted { $0.createdAt > $1.createdAt }
    }

    func rebuildIndex() throws -> Int {
        let files = try allMarkdownFiles(in: paths.vaultRoot)
        let records = try files.map { url -> [String: String] in
            let content = try String(contentsOf: url, encoding: .utf8)
            return [
                "path": url.path,
                "title": title(from: content, fallback: url.deletingPathExtension().lastPathComponent),
                "excerpt": excerpt(from: content)
            ]
        }
        let data = try JSONSerialization.data(withJSONObject: records, options: [.prettyPrinted, .sortedKeys])
        try fileManager.createDirectory(at: paths.supportRoot, withIntermediateDirectories: true)
        try data.write(to: paths.indexFile, options: .atomic)
        return records.count
    }

    private func writeSeedIfNeeded(at url: URL, title: String, type: String, body: String) throws {
        guard !fileManager.fileExists(atPath: url.path) else { return }
        try markdown(title: title, type: type, tags: [], body: body).write(to: url, atomically: true, encoding: .utf8)
    }

    private func markProposal(_ proposal: ReviewProposal, status: ReviewProposal.Status) throws {
        var content = try String(contentsOf: proposal.path, encoding: .utf8)
        if content.contains("status: pending") {
            content = content.replacingOccurrences(of: "status: pending", with: "status: \(status.rawValue)")
        } else {
            content += "\n\nstatus: \(status.rawValue)\n"
        }
        try content.write(to: proposal.path, atomically: true, encoding: .utf8)
    }

    private func markdown(title: String, type: String, tags: [String], body: String) -> String {
        """
        ---
        title: \(escapeYaml(title))
        type: \(type)
        tags: [\(tags.map(escapeYaml).joined(separator: ", "))]
        created_at: \(ISO8601DateFormatter().string(from: Date()))
        ---

        \(body)
        """
    }

    private func listMarkdown(in directory: URL) throws -> [URL] {
        guard fileManager.fileExists(atPath: directory.path) else { return [] }
        return try fileManager.contentsOfDirectory(at: directory, includingPropertiesForKeys: [.creationDateKey])
            .filter { $0.pathExtension == "md" }
    }

    private func allMarkdownFiles(in directory: URL) throws -> [URL] {
        guard let enumerator = fileManager.enumerator(at: directory, includingPropertiesForKeys: nil) else { return [] }
        return enumerator.compactMap { $0 as? URL }.filter { $0.pathExtension == "md" }
    }

    private func note(from url: URL) -> WorkbenchNote {
        let content = (try? String(contentsOf: url, encoding: .utf8)) ?? ""
        return WorkbenchNote(
            id: UUID(),
            title: title(from: content, fallback: url.deletingPathExtension().lastPathComponent),
            body: body(from: content),
            path: url,
            createdAt: creationDate(url),
            tags: []
        )
    }

    private func proposal(from url: URL) -> ReviewProposal {
        let content = (try? String(contentsOf: url, encoding: .utf8)) ?? ""
        let status: ReviewProposal.Status
        if content.contains("status: approved") {
            status = .approved
        } else if content.contains("status: rejected") {
            status = .rejected
        } else {
            status = .pending
        }

        return ReviewProposal(
            id: UUID(),
            title: title(from: content, fallback: url.deletingPathExtension().lastPathComponent),
            body: body(from: content),
            source: frontmatterValue("source", in: content) ?? "agent",
            status: status,
            path: url,
            createdAt: creationDate(url)
        )
    }

    private func title(from content: String, fallback: String) -> String {
        frontmatterValue("title", in: content) ?? content
            .split(separator: "\n")
            .first(where: { $0.hasPrefix("# ") })?
            .dropFirst(2)
            .description ?? fallback
    }

    private func body(from content: String) -> String {
        if let range = content.range(of: "---", options: [], range: content.index(after: content.startIndex)..<content.endIndex) {
            return String(content[range.upperBound...]).trimmingCharacters(in: .whitespacesAndNewlines)
        }
        return content
    }

    private func excerpt(from content: String) -> String {
        body(from: content)
            .replacingOccurrences(of: "\n", with: " ")
            .prefix(280)
            .description
    }

    private func frontmatterValue(_ key: String, in content: String) -> String? {
        content.split(separator: "\n").first { $0.hasPrefix("\(key):") }?
            .replacingOccurrences(of: "\(key):", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func creationDate(_ url: URL) -> Date {
        ((try? url.resourceValues(forKeys: [.creationDateKey]))?.creationDate) ?? Date.distantPast
    }

    private func timestampSlug() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd-HHmmss"
        return formatter.string(from: Date())
    }

    private func slugify(_ value: String) -> String {
        let allowed = CharacterSet.alphanumerics.union(CharacterSet(charactersIn: "-_"))
        return value
            .lowercased()
            .replacingOccurrences(of: " ", with: "-")
            .unicodeScalars
            .map { allowed.contains($0) ? Character($0) : "-" }
            .reduce("") { $0 + String($1) }
            .replacingOccurrences(of: "--", with: "-")
            .trimmingCharacters(in: CharacterSet(charactersIn: "-"))
    }

    private func escapeYaml(_ value: String) -> String {
        "\"\(value.replacingOccurrences(of: "\"", with: "\\\""))\""
    }
}
