import Foundation
import Observation

@Observable
final class WorkbenchStore {
    var selection: SidebarItem? = .inbox
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
        Improve or act on this typed Tremotino object according to its contents. You may directly edit typed private Tremotino vault objects. Keep changes scoped to the writable paths and preserve the Markdown/frontmatter structure.

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
            let ignore = paths.vaultRoot.appendingPathComponent(".gitignore")
            if !FileManager.default.fileExists(atPath: ignore.path) {
                try """
                .DS_Store
                *.tmp
                """.write(to: ignore, atomically: true, encoding: .utf8)
            }

            guard !FileManager.default.fileExists(atPath: paths.vaultRoot.appendingPathComponent(".git").path) else {
                statusMessage = "Vault Git backup already initialized"
                return
            }

            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/usr/bin/git")
            process.arguments = ["init"]
            process.currentDirectoryURL = paths.vaultRoot
            try process.run()
            process.waitUntilExit()
            statusMessage = process.terminationStatus == 0 ? "Initialized Git backup in vault" : "Git init failed with status \(process.terminationStatus)"
        } catch {
            statusMessage = "Git backup setup failed: \(error.localizedDescription)"
        }
    }

    private func seedRunbooks() {
        runbooks = [
            Runbook(id: "rebuild-index", title: "Rebuild Index", detail: "Rebuild disposable search metadata from Markdown.", commandPreview: "tremotino rebuild-index"),
            Runbook(id: "scan-projects", title: "Scan Known Projects", detail: "Read local project folders and create review proposals.", commandPreview: "tremotino scan-projects --dry-run"),
            Runbook(id: "registry-refresh", title: "Refresh MCP Registry", detail: "Fetch registry/spec/roadmap status without installing servers.", commandPreview: "tremotino registry-refresh")
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
