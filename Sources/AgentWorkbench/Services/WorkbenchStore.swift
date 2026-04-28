import Foundation
import Observation

@Observable
final class WorkbenchStore {
    var selection: SidebarItem? = .capture
    var showQuickCapture = false
    var captureTitle = ""
    var captureBody = ""
    var statusMessage = "Booting Tremotino"
    var inboxNotes: [WorkbenchNote] = []
    var proposals: [ReviewProposal] = []
    var projects: [WorkbenchProject] = []
    var workflows: [VaultDocument] = []
    var prompts: [VaultDocument] = []
    var profiles: [VaultDocument] = []
    var directories: [VaultDocument] = []
    var bibliographies: [VaultDocument] = []
    var skills: [VaultDocument] = []
    var plugins: [VaultDocument] = []
    var designs: [VaultDocument] = []
    var stills: [VaultDocument] = []
    var contextPacks: [VaultDocument] = []
    var hayItems: [VaultDocument] = []
    var goldItems: [VaultDocument] = []
    var codexJobs: [CodexJob] = []
    var registrySnapshots: [RegistrySnapshot] = []
    var runbooks: [Runbook] = []
    var indexCount = 0
    var mcpHealth = "Not checked"

    let paths = WorkbenchPaths.defaults
    private var markdownStore: MarkdownStore { MarkdownStore(paths: paths) }

    func bootstrap() async {
        do {
            try markdownStore.bootstrapVault()
            seedRunbooks()
            seedProjects()
            try refresh()
            indexCount = try markdownStore.rebuildIndex()
            mcpHealth = FileManager.default.fileExists(atPath: paths.mcpServer.path) ? "Available at \(paths.mcpServer.path)" : "Missing MCP server"
            statusMessage = "Vault ready at \(paths.vaultRoot.path)"
        } catch {
            statusMessage = "Bootstrap failed: \(error.localizedDescription)"
        }
    }

    func refresh() throws {
        inboxNotes = try markdownStore.listInboxNotes()
        proposals = try markdownStore.listReviewProposals()
        workflows = try markdownStore.listDocuments(type: .workflow)
        prompts = try markdownStore.listDocuments(type: .prompt)
        profiles = try markdownStore.listDocuments(type: .profile)
        directories = try markdownStore.listDocuments(type: .directory)
        bibliographies = try markdownStore.listDocuments(type: .bibliography)
        skills = try markdownStore.listDocuments(type: .skill)
        plugins = try markdownStore.listDocuments(type: .plugin)
        designs = try markdownStore.listDocuments(type: .designMD)
        stills = try markdownStore.listDocuments(type: .still)
        contextPacks = try markdownStore.listDocuments(type: .contextPack)
        hayItems = try markdownStore.listDocuments(type: .hay)
        goldItems = try markdownStore.listDocuments(type: .gold)
        codexJobs = try markdownStore.listCodexJobs()
    }

    func saveCapture() {
        do {
            try markdownStore.createInboxNote(title: captureTitle, body: captureBody, tags: ["capture"])
            captureTitle = ""
            captureBody = ""
            showQuickCapture = false
            try refresh()
            statusMessage = "Captured to Inbox"
        } catch {
            statusMessage = "Capture failed: \(error.localizedDescription)"
        }
    }

    func rebuildIndex() async {
        do {
            indexCount = try markdownStore.rebuildIndex()
            try refresh()
            statusMessage = "Rebuilt index from \(indexCount) Markdown files"
        } catch {
            statusMessage = "Index rebuild failed: \(error.localizedDescription)"
        }
    }

    func approve(_ proposal: ReviewProposal) {
        do {
            try markdownStore.approveProposal(proposal)
            try refresh()
            statusMessage = "Approved proposal"
        } catch {
            statusMessage = "Approval failed: \(error.localizedDescription)"
        }
    }

    func reject(_ proposal: ReviewProposal) {
        do {
            try markdownStore.rejectProposal(proposal)
            try refresh()
            statusMessage = "Rejected proposal"
        } catch {
            statusMessage = "Reject failed: \(error.localizedDescription)"
        }
    }

    func saveDocument(_ document: VaultDocument) {
        do {
            try markdownStore.saveDocument(document)
            try refresh()
            statusMessage = "Saved \(document.type.title.lowercased())"
        } catch {
            statusMessage = "Save failed: \(error.localizedDescription)"
        }
    }

    func createDocument(type: VaultObjectType) {
        do {
            let title = "Untitled \(type.title)"
            let body: String
            switch type {
            case .designMD:
                body = "# \(title)\n\n## Visual Direction\n\n## Typography\n\n## Components\n\n## Agent Guidance\n"
            case .still:
                body = "# \(title)\n\nsource:\nlicense_privacy: private\nmedia_path: Files/\nrelated_workflow:\nintended_agent_use:\n\n## Notes\n"
            case .contextPack:
                body = "# \(title)\n\n## Includes\n- Operating profile\n- Prompt pack\n- Workflows\n- Design\n- Stills\n- Gold\n\n## Task Fit\n"
            case .hay:
                body = "# \(title)\n\n## Raw Material\n\n## Extraction Goal\n\n## Output Preference\nPrefer durable Gold, typed prompts, workflows, profile updates, directory notes, or review proposals depending on risk.\n"
            case .bibliography:
                body = "# \(title)\n\n## Citation Metadata\n- bibtex_key:\n- entry_type:\n- authors:\n- year:\n- doi:\n- url:\n- source:\n\n## Agent Notes\n\n## Raw BibTeX\n```bibtex\n\n```\n"
            case .plugin:
                body = "# \(title)\n\n## Purpose\n\n## Contents\n\n## Install Policy\nNo executable code. Import approved Markdown assets only.\n"
            case .skill:
                body = "# \(title)\n\n## Purpose\n\n## When To Use\n\n## Instructions\n"
            default:
                body = "# \(title)\n"
            }
            try markdownStore.createDocument(type: type, title: title, body: body)
            try refresh()
            statusMessage = "Created \(type.title.lowercased())"
        } catch {
            statusMessage = "Create failed: \(error.localizedDescription)"
        }
    }

    func assembleContextPack(_ pack: VaultDocument, client: String) -> String {
        let promptMatches = prompts.filter { document in
            let name = document.path.deletingPathExtension().lastPathComponent.lowercased()
            return name.contains("shared") || name.contains("writing") || name.contains(client.lowercased())
        }
        let sections = [
            "# Tremotino Context Pack",
            "Client: \(client)",
            "## Pack\n\(pack.body)",
            "## Operating Profile\n\(profiles.map { $0.body }.joined(separator: "\n\n---\n\n"))",
            "## Prompt Pack\n\(promptMatches.map { $0.body }.joined(separator: "\n\n---\n\n"))",
            "## Design\n\(designs.map { $0.body }.joined(separator: "\n\n---\n\n"))",
            "## Stills\n\(stills.map { "\($0.title)\nPath: \($0.path.path)\n\n\($0.body)" }.joined(separator: "\n\n---\n\n"))",
            "## Bibliography\n\(bibliographies.prefix(12).map { "\($0.title)\nPath: \($0.path.path)\n\n\($0.body.prefix(1200))" }.joined(separator: "\n\n---\n\n"))",
            "## Hay\n\(hayItems.prefix(8).map { $0.body }.joined(separator: "\n\n---\n\n"))",
            "## Gold\n\(goldItems.prefix(8).map { $0.body }.joined(separator: "\n\n---\n\n"))"
        ]
        return sections.joined(separator: "\n\n")
    }

    func createCodexJob(from contextPack: VaultDocument, client: String = "codex") {
        let prompt = """
        You are running from Tremotino using an assembled context pack.

        Use the following context to propose or perform scoped work inside the Tremotino vault. Keep edits limited to typed vault objects unless a workflow explicitly grants another writable path.

        \(assembleContextPack(contextPack, client: client))
        """

        do {
            _ = try markdownStore.createCodexJob(
                title: "Context pack: \(contextPack.title)",
                workflow: contextPack.title,
                prompt: prompt,
                workingDirectory: paths.vaultRoot.path,
                writablePaths: [paths.vaultRoot.path]
            )
            try refresh()
            statusMessage = "Queued Codex job from context pack"
        } catch {
            statusMessage = "Job creation failed: \(error.localizedDescription)"
        }
    }

    func importBibTeX(from url: URL) {
        do {
            let imported = try markdownStore.importBibTeXFile(url)
            try refresh()
            statusMessage = "Imported \(imported) BibTeX entries"
        } catch {
            statusMessage = "BibTeX import failed: \(error.localizedDescription)"
        }
    }

    func validateBibliography() {
        statusMessage = markdownStore.validateBibliography(bibliographies)
    }

    func createBibliographyReviewJob() {
        let prompt = """
        You are running from Tremotino.

        Review the Tremotino bibliography library as first-class research memory. Identify duplicate keys, missing DOI/URL/year/author metadata, citation-integrity risks, and entries that should be linked to Gold or research projects.

        Write outputs only inside the Tremotino vault. Prefer Review proposals for uncertain durable claims.

        Bibliography entries:
        \(bibliographies.map { "## \($0.title)\nPath: \($0.path.path)\n\n\($0.body.prefix(1600))" }.joined(separator: "\n\n---\n\n"))
        """

        do {
            _ = try markdownStore.createCodexJob(
                title: "Review bibliography library",
                workflow: "Bibliography Management",
                prompt: prompt,
                workingDirectory: paths.vaultRoot.path,
                writablePaths: [paths.vaultRoot.path]
            )
            try refresh()
            statusMessage = "Queued bibliography review job"
        } catch {
            statusMessage = "Bibliography job failed: \(error.localizedDescription)"
        }
    }

    func createHayIngestionJob(from hay: VaultDocument, sourcePaths: [String]) {
        let expandedSources = sourcePaths
            .map { NSString(string: $0).expandingTildeInPath }
            .filter { !$0.isEmpty }
        let prompt = """
        You are running from Tremotino.

        Spin hay into gold: inspect the provided files or folders as disordered raw material, extract durable signal, and write the refined result into the Tremotino vault.

        Treat source paths as read-only raw material. Do not edit, delete, move, rename, or reformat source files. Write outputs only inside the Tremotino vault.

        Source paths:
        \(expandedSources.map { "- \($0)" }.joined(separator: "\n"))

        Hay sidecar:
        \(hay.title)

        \(hay.body)

        Output rules:
        - Create Gold items for reusable claims, arguments, summaries, or research signal.
        - Create typed prompts, workflows, profile notes, directory notes, or review proposals only when clearly useful.
        - Preserve source paths and uncertainty.
        - Keep private data in the vault; do not add anything to the public Tremotino repo.
        """

        do {
            _ = try markdownStore.createCodexJob(
                title: "Spin hay into gold: \(hay.title)",
                workflow: "Hay Ingestion",
                prompt: prompt,
                workingDirectory: paths.vaultRoot.path,
                writablePaths: [paths.vaultRoot.path],
                sourcePaths: expandedSources
            )
            try refresh()
            statusMessage = "Queued hay ingestion job"
        } catch {
            statusMessage = "Hay ingestion job failed: \(error.localizedDescription)"
        }
    }

    func spinIntoGold(title: String, body: String, source: String) {
        do {
            try markdownStore.createGold(title: title, body: body, source: source)
            try refresh()
            statusMessage = "Spun raw material into Gold"
        } catch {
            statusMessage = "Gold creation failed: \(error.localizedDescription)"
        }
    }

    func createCodexJob(from document: VaultDocument) {
        let workingDirectory = paths.vaultRoot.path
        let prompt = """
        You are running from Tremotino, a local agent operating hub.

        Workflow/Object:
        \(document.title)

        Object type:
        \(document.type.rawValue)

        Task:
        \(codexInstruction(for: document))

        Content:
        \(document.body)
        """

        do {
            _ = try markdownStore.createCodexJob(
                title: "Codex: \(document.title)",
                workflow: document.title,
                prompt: prompt,
                workingDirectory: workingDirectory,
                writablePaths: [paths.vaultRoot.path]
            )
            try refresh()
            statusMessage = "Queued Codex job"
        } catch {
            statusMessage = "Job creation failed: \(error.localizedDescription)"
        }
    }

    private func codexInstruction(for document: VaultDocument) -> String {
        if document.type == .hay {
            return """
            Extract signal from this disordered raw material. Turn reusable outputs into Gold, typed prompts, workflows, profile notes, directory notes, or review proposals. Preserve provenance, uncertainty, and source paths. Do not flatten uncertain claims into facts.
            """
        }
        if document.type == .bibliography {
            return """
            Treat this bibliography entry as source metadata. Verify completeness, normalize notes, preserve the raw BibTeX block, and propose links to relevant Gold, research projects, or context packs. Do not invent DOI, author, year, or publication metadata.
            """
        }
        return """
        Improve or act on this typed Tremotino object according to its contents. You may directly edit typed private Tremotino vault objects. Keep changes scoped to the writable paths and preserve the Markdown/frontmatter structure.
        """
    }

    func createCodexJob(from note: WorkbenchNote) {
        let prompt = """
        You are running from Tremotino.

        Convert this raw inbox item into a useful typed Tremotino object. Prefer `gold`, `workflow`, `prompt`, `profile`, or `directory` depending on the content. Edit only the Tremotino vault.

        Inbox item:
        \(note.title)

        \(note.body)
        """

        do {
            _ = try markdownStore.createCodexJob(
                title: "Spin inbox into gold: \(note.title)",
                workflow: "Spin Into Gold",
                prompt: prompt,
                workingDirectory: paths.vaultRoot.path,
                writablePaths: [paths.vaultRoot.path]
            )
            try refresh()
            statusMessage = "Queued Codex job from inbox"
        } catch {
            statusMessage = "Job creation failed: \(error.localizedDescription)"
        }
    }

    func runCodexJob(_ job: CodexJob) {
        Task {
            do {
                try markdownStore.updateCodexJob(job, status: "running", startedAt: Date())
                try refresh()
                let exitCode = await CodexJobRunner(vaultRoot: paths.vaultRoot).run(job: job)
                let refreshedJob = (try? markdownStore.listCodexJobs().first { $0.path == job.path }) ?? job
                try markdownStore.updateCodexJob(refreshedJob, status: exitCode == 0 ? "completed" : "failed", finishedAt: Date(), exitCode: Int(exitCode))
                try refresh()
                statusMessage = "Codex job finished with exit \(exitCode)"
            } catch {
                statusMessage = "Codex job failed: \(error.localizedDescription)"
            }
        }
    }

    func scanKnownProjects() {
        let candidates = [
            ("Personal Site", "~/Documents/GitHub/index", ProjectKind.localApp),
            ("Land Explorer", "~/Documents/GitHub/land_explorer", ProjectKind.localApp),
            ("Monti Prenestini Report", "~/Documents/GitHub/REPORT MONTI PRENESTINI", ProjectKind.researchReport),
            ("Confinvest", "~/Library/CloudStorage/GoogleDrive-gbrlpizzi@gmail.com/My Drive/Confinvest", ProjectKind.generic)
        ]

        var created = 0
        for candidate in candidates {
            let expanded = NSString(string: candidate.1).expandingTildeInPath
            guard FileManager.default.fileExists(atPath: expanded) else { continue }
            let summary = ProjectScanner().summarize(path: URL(fileURLWithPath: expanded), kind: candidate.2)
            do {
                try markdownStore.createProposal(
                    title: "Proposal: \(candidate.0) project memory",
                    body: summary,
                    source: "local-project-ingestion"
                )
                created += 1
            } catch {
                statusMessage = "Project scan failed: \(error.localizedDescription)"
            }
        }

        do {
            try refresh()
            statusMessage = "Created \(created) project memory proposals"
        } catch {
            statusMessage = "Refresh failed: \(error.localizedDescription)"
        }
    }

    func refreshRegistry() async {
        let endpoints = [
            URL(string: "https://registry.modelcontextprotocol.io/")!,
            URL(string: "https://modelcontextprotocol.io/specification/2025-11-25/basic")!,
            URL(string: "https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/")!
        ]

        var snapshots: [RegistrySnapshot] = []
        for endpoint in endpoints {
            do {
                let (_, response) = try await URLSession.shared.data(from: endpoint)
                let status: String
                if let http = response as? HTTPURLResponse {
                    status = "HTTP \(http.statusCode)"
                } else {
                    status = "Fetched"
                }
                snapshots.append(RegistrySnapshot(title: endpoint.host() ?? endpoint.absoluteString, detail: endpoint.absoluteString, fetchedAt: Date(), url: endpoint, status: status))
            } catch {
                snapshots.append(RegistrySnapshot(title: endpoint.host() ?? endpoint.absoluteString, detail: error.localizedDescription, fetchedAt: Date(), url: endpoint, status: "Failed"))
            }
        }
        registrySnapshots = snapshots
        statusMessage = "Registry monitor refreshed"
    }

    func initializeVaultGitBackup() {
        do {
            let alreadyInitialized = FileManager.default.fileExists(atPath: paths.vaultRoot.appendingPathComponent(".git").path)
            try ensureVaultGitBackup()
            statusMessage = alreadyInitialized ? "Vault Git backup already initialized" : "Initialized Git backup in vault"
        } catch {
            statusMessage = "Git backup setup failed: \(error.localizedDescription)"
        }
    }

    func configureVaultGitRemote(_ remoteURL: String) {
        do {
            try ensureVaultGitBackup()
            let trimmed = remoteURL.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !trimmed.isEmpty else {
                statusMessage = "Remote URL is empty"
                return
            }
            if runGit(["remote", "get-url", "origin"]).exitCode == 0 {
                let result = try runGitChecked(["remote", "set-url", "origin", trimmed])
                statusMessage = result.output.isEmpty ? "Updated vault Git remote" : result.output
            } else {
                let result = try runGitChecked(["remote", "add", "origin", trimmed])
                statusMessage = result.output.isEmpty ? "Added vault Git remote" : result.output
            }
        } catch {
            statusMessage = "Remote setup failed: \(error.localizedDescription)"
        }
    }

    func snapshotVaultGitBackup(message: String) {
        do {
            try ensureVaultGitBackup()
            _ = try runGitChecked(["add", "-A"])
            let status = try runGitChecked(["status", "--short"]).output
            guard !status.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                statusMessage = "Vault backup has no changes"
                return
            }
            let trimmed = message.trimmingCharacters(in: .whitespacesAndNewlines)
            let commitMessage = trimmed.isEmpty ? "Tremotino vault snapshot" : trimmed
            _ = try runGitChecked(["commit", "-m", commitMessage])
            statusMessage = "Committed vault backup snapshot"
        } catch {
            statusMessage = "Vault snapshot failed: \(error.localizedDescription)"
        }
    }

    func pushVaultGitBackup() {
        do {
            try ensureVaultGitBackup()
            let remote = runGit(["remote", "get-url", "origin"])
            guard remote.exitCode == 0, !remote.output.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                statusMessage = "No private remote configured"
                return
            }
            _ = try runGitChecked(["push", "-u", "origin", "main"])
            statusMessage = "Pushed vault backup to private remote"
        } catch {
            statusMessage = "Vault push failed: \(error.localizedDescription)"
        }
    }

    private func ensureVaultGitBackup() throws {
        let ignore = paths.vaultRoot.appendingPathComponent(".gitignore")
        if !FileManager.default.fileExists(atPath: ignore.path) {
            try """
            .DS_Store
            *.tmp
            .tremotino-backup
            """.write(to: ignore, atomically: true, encoding: .utf8)
        }

        if !FileManager.default.fileExists(atPath: paths.vaultRoot.appendingPathComponent(".git").path) {
            _ = try runGitChecked(["init"])
            _ = try runGitChecked(["branch", "-M", "main"])
        }
    }

    private func runGitChecked(_ arguments: [String]) throws -> (exitCode: Int32, output: String) {
        let result = runGit(arguments)
        guard result.exitCode == 0 else {
            throw NSError(domain: "TremotinoGit", code: Int(result.exitCode), userInfo: [NSLocalizedDescriptionKey: result.output])
        }
        return result
    }

    private func runGit(_ arguments: [String]) -> (exitCode: Int32, output: String) {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/git")
        process.arguments = arguments
        process.currentDirectoryURL = paths.vaultRoot
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        do {
            try process.run()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            process.waitUntilExit()
            let output = String(data: data, encoding: .utf8) ?? ""
            return (process.terminationStatus, output.trimmingCharacters(in: .whitespacesAndNewlines))
        } catch {
            return (-1, error.localizedDescription)
        }
    }

    private func seedRunbooks() {
        runbooks = [
            Runbook(id: "rebuild-index", title: "Rebuild Index", detail: "Rebuild disposable search metadata from Markdown.", commandPreview: "tremotino rebuild-index"),
            Runbook(id: "scan-projects", title: "Scan Known Projects", detail: "Read local project folders and create review proposals.", commandPreview: "tremotino scan-projects --dry-run"),
            Runbook(id: "registry-refresh", title: "Refresh MCP Registry", detail: "Fetch registry/spec/roadmap status without installing servers.", commandPreview: "tremotino registry-refresh"),
            Runbook(id: "backup-vault", title: "Backup Private Vault", detail: "Commit and push the private Markdown vault to its configured Git remote.", commandPreview: "./script/backup_vault.sh \"Tremotino vault snapshot\"")
        ]
    }

    private func seedProjects() {
        projects = [
            WorkbenchProject(id: UUID(), title: "Research Moat Hub", kind: .researchMoat, path: "~/Documents/Tremotino/Vault/Projects/research-moat-hub.md", summary: "Second-brain layer for sources, claims, reusable arguments, people, institutions, and project evidence.", updatedAt: Date()),
            WorkbenchProject(id: UUID(), title: "Grant & Applications", kind: .grantApplication, path: "~/Documents/Career General", summary: "Drafting, application answers, public positioning, and source links.", updatedAt: Date()),
            WorkbenchProject(id: UUID(), title: "Land Explorer", kind: .localApp, path: "~/Documents/GitHub/land_explorer", summary: "Platform rebuilds, validation, runtime assets, and demo readiness.", updatedAt: Date()),
            WorkbenchProject(id: UUID(), title: "Research Packs", kind: .researchReport, path: "~/Downloads/Monti Prenestini ricerca 4", summary: "Source compaction, report packages, and provenance checks.", updatedAt: Date())
        ]
    }
}
