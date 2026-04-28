import Foundation

struct MarkdownStore {
    var paths: WorkbenchPaths
    private let fileManager = FileManager.default

    func bootstrapVault() throws {
        for directory in [
            paths.vaultRoot,
            paths.inbox,
            paths.workflows,
            paths.prompts,
            paths.profile,
            paths.directories,
            paths.jobs,
            paths.projects,
            paths.review,
            paths.runbooks,
            paths.gold,
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
            at: paths.profile.appendingPathComponent("how-i-work.md"),
            title: "How I Work",
            type: "profile",
            body: """
            # How I Work

            This private profile tells agents how to collaborate with me.

            ## Collaboration Defaults
            - Prefer direct implementation once the goal is clear.
            - Keep uncertainty visible when facts, data, or claims are not fully verified.
            - Use local authoritative artifacts before rebuilding ingestion paths.

            ## Edit Authority
            Codex jobs may directly edit typed Tremotino objects when launched from the Jobs view. Unknown or high-risk durable memory should still be proposed through Review.
            """
        )

        try writeSeedIfNeeded(
            at: paths.profile.appendingPathComponent("what-i-do.md"),
            title: "What I Do",
            type: "profile",
            body: """
            # What I Do

            A private operating note for recurring domains, projects, research themes, and working context.

            ## Themes
            - Territorial intelligence
            - Land stewardship
            - Research workflows
            - Agent-native software
            """
        )

        try writeSeedIfNeeded(
            at: paths.prompts.appendingPathComponent("shared-operating-prompt.md"),
            title: "Shared Operating Prompt",
            type: "prompt",
            body: """
            # Shared Operating Prompt

            Use this as the shared agent operating layer before applying client-specific instructions.

            ## Core
            Act as a pragmatic implementation partner. Preserve provenance, avoid overwriting private context casually, and turn raw material into durable useful context.
            """
        )

        try writeSeedIfNeeded(
            at: paths.prompts.appendingPathComponent("writing-style-guide.md"),
            title: "Writing Style Guide",
            type: "prompt",
            body: """
            # Writing Style Guide

            ## Purpose
            Reusable writing guidance for agents drafting on my behalf.

            ## Defaults
            - Use direct, concrete language.
            - Avoid generic motivational phrasing.
            - Keep claims grounded in source material.
            - Preserve uncertainty where it matters.

            ## Usage
            Include this in prompt packs for outreach, applications, reports, public copy, and research summaries.
            """
        )

        try writeSeedIfNeeded(
            at: paths.prompts.appendingPathComponent("system-prompt-library.md"),
            title: "System Prompt Library",
            type: "prompt",
            body: """
            # System Prompt Library

            A private collection of reusable system prompts and operating instructions for Codex, Claude, and future agents.

            ## Entries
            Add stable prompts here or split them into individual prompt files when they become important enough to version separately.
            """
        )

        try writeSeedIfNeeded(
            at: paths.prompts.appendingPathComponent("codex-adapter.md"),
            title: "Codex Adapter",
            type: "prompt",
            body: """
            # Codex Adapter

            Codex can inspect repositories, edit files, run tests, and launch scoped jobs. Prefer real source-of-truth edits and verification.
            """
        )

        try writeSeedIfNeeded(
            at: paths.prompts.appendingPathComponent("claude-adapter.md"),
            title: "Claude Adapter",
            type: "prompt",
            body: """
            # Claude Adapter

            Claude should use Tremotino MCP tools to retrieve workflows, prompts, and profile context before answering or drafting.
            """
        )

        try writeSeedIfNeeded(
            at: paths.workflows.appendingPathComponent("project-briefing.md"),
            title: "Project Briefing",
            type: "workflow",
            body: """
            # Project Briefing

            ## Purpose
            Assemble the right context for an agent before it starts work.

            ## Inputs
            - Project or directory name
            - User request
            - Relevant workflow or prompt pack

            ## Steps
            1. Fetch operating profile.
            2. Fetch relevant directory/project context.
            3. Search gold items and prior decisions.
            4. Produce a concise execution brief.

            ## Expected Output
            A short, source-aware brief that can be handed to Codex or Claude.
            """
        )

        try writeSeedIfNeeded(
            at: paths.workflows.appendingPathComponent("spin-into-gold.md"),
            title: "Spin Into Gold",
            type: "workflow",
            body: """
            # Spin Into Gold

            ## Purpose
            Convert raw hay such as notes, transcripts, folders, or agent outputs into durable reusable context.

            ## Steps
            1. Identify the reusable claim, workflow, prompt, or research item.
            2. Preserve source path and uncertainty.
            3. Write a compact gold item.
            4. Link it back to the originating material.
            """
        )

        try writeSeedIfNeeded(
            at: paths.directories.appendingPathComponent("local-projects.md"),
            title: "Local Projects",
            type: "directory",
            body: """
            # Local Projects

            Manual registry of important local folders. Add private paths here with purpose, privacy, and allowed scan/edit policy.

            ## Entries
            - path: ~/Documents/GitHub
              purpose: Local development projects
              privacy: private
              policy: ask before broad scans
            """
        )

        try writeSeedIfNeeded(
            at: paths.gold.appendingPathComponent("README.md"),
            title: "Gold",
            type: "gold",
            body: """
            # Gold

            Refined reusable context belongs here: source-backed claims, stable workflows, durable project briefs, and prompts that have survived review.
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

    func createGold(title: String, body: String, source: String) throws {
        let filename = "\(timestampSlug())-\(slugify(title)).md"
        let url = paths.gold.appendingPathComponent(filename)
        let content = """
        ---
        title: \(escapeYaml(title))
        type: gold
        source: \(escapeYaml(source))
        created_at: \(ISO8601DateFormatter().string(from: Date()))
        ---

        # \(title)

        \(body)
        """
        try content.write(to: url, atomically: true, encoding: .utf8)
    }

    func createCodexJob(title: String, workflow: String, prompt: String, workingDirectory: String, writablePaths: [String]) throws -> CodexJob {
        let folder = paths.jobs.appendingPathComponent("\(timestampSlug())-\(slugify(title))")
        try fileManager.createDirectory(at: folder, withIntermediateDirectories: true)
        let jobFile = folder.appendingPathComponent("job.md")
        let promptFile = folder.appendingPathComponent("prompt.md")
        let content = codexJobMarkdown(
            title: title,
            status: "queued",
            workflow: workflow,
            workingDirectory: workingDirectory,
            writablePaths: writablePaths,
            startedAt: nil,
            finishedAt: nil,
            exitCode: nil
        )
        try content.write(to: jobFile, atomically: true, encoding: .utf8)
        try prompt.write(to: promptFile, atomically: true, encoding: .utf8)
        return try codexJob(from: jobFile)
    }

    func updateCodexJob(_ job: CodexJob, status: String, startedAt: Date? = nil, finishedAt: Date? = nil, exitCode: Int? = nil) throws {
        let content = codexJobMarkdown(
            title: job.title,
            status: status,
            workflow: job.workflow,
            workingDirectory: job.workingDirectory,
            writablePaths: job.writablePaths,
            startedAt: startedAt,
            finishedAt: finishedAt,
            exitCode: exitCode
        )
        try content.write(to: job.path, atomically: true, encoding: .utf8)
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

    func listDocuments(type: VaultObjectType) throws -> [VaultDocument] {
        let directory = directory(for: type)
        return try listMarkdown(in: directory).map { document(from: $0, type: type) }
            .sorted { $0.createdAt > $1.createdAt }
    }

    func saveDocument(_ document: VaultDocument) throws {
        let content = markdown(title: document.title, type: document.type.rawValue, tags: [], body: document.body)
        try content.write(to: document.path, atomically: true, encoding: .utf8)
    }

    func listCodexJobs() throws -> [CodexJob] {
        guard fileManager.fileExists(atPath: paths.jobs.path) else { return [] }
        let folders = try fileManager.contentsOfDirectory(at: paths.jobs, includingPropertiesForKeys: [.creationDateKey])
            .filter { $0.hasDirectoryPath }
        return try folders.compactMap { folder in
            let jobFile = folder.appendingPathComponent("job.md")
            guard fileManager.fileExists(atPath: jobFile.path) else { return nil }
            return try codexJob(from: jobFile)
        }
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

    private func directory(for type: VaultObjectType) -> URL {
        switch type {
        case .workflow: paths.workflows
        case .prompt: paths.prompts
        case .profile: paths.profile
        case .directory: paths.directories
        case .codexJob: paths.jobs
        case .gold: paths.gold
        }
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

    private func document(from url: URL, type: VaultObjectType) -> VaultDocument {
        let content = (try? String(contentsOf: url, encoding: .utf8)) ?? ""
        return VaultDocument(
            id: UUID(),
            title: title(from: content, fallback: url.deletingPathExtension().lastPathComponent),
            type: type,
            body: body(from: content),
            path: url,
            createdAt: creationDate(url),
            status: frontmatterValue("status", in: content)
        )
    }

    private func codexJob(from url: URL) throws -> CodexJob {
        let content = try String(contentsOf: url, encoding: .utf8)
        let writable = (frontmatterValue("writable_paths", in: content) ?? "")
            .split(separator: "|")
            .map { String($0).trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
        let exitCode = frontmatterValue("exit_code", in: content).flatMap(Int.init)
        return CodexJob(
            id: UUID(),
            title: title(from: content, fallback: url.deletingPathExtension().lastPathComponent),
            status: frontmatterValue("status", in: content) ?? "queued",
            workflow: frontmatterValue("workflow", in: content) ?? "manual",
            workingDirectory: frontmatterValue("working_directory", in: content) ?? paths.vaultRoot.path,
            writablePaths: writable,
            path: url,
            createdAt: creationDate(url),
            exitCode: exitCode
        )
    }

    private func codexJobMarkdown(
        title: String,
        status: String,
        workflow: String,
        workingDirectory: String,
        writablePaths: [String],
        startedAt: Date?,
        finishedAt: Date?,
        exitCode: Int?
    ) -> String {
        let formatter = ISO8601DateFormatter()
        return """
        ---
        title: \(escapeYaml(title))
        type: codex_job
        status: \(status)
        workflow: \(escapeYaml(workflow))
        client: codex
        working_directory: \(escapeYaml(workingDirectory))
        sandbox: workspace-write
        writable_paths: \(escapeYaml(writablePaths.joined(separator: "|")))
        created_at: \(formatter.string(from: Date()))
        started_at: \(startedAt.map(formatter.string(from:)) ?? "")
        finished_at: \(finishedAt.map(formatter.string(from:)) ?? "")
        exit_code: \(exitCode.map(String.init) ?? "")
        ---

        # \(title)

        Job artifacts live next to this file:
        - `prompt.md`
        - `events.jsonl`
        - `final.md`
        - `pre_snapshot.txt`
        - `post_snapshot.txt`
        """
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
