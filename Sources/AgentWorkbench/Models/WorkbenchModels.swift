import Foundation

enum SidebarItem: String, CaseIterable, Identifiable {
    case spin
    case library
    case agents
    case review

    var id: String { rawValue }

    var title: String {
        switch self {
        case .spin: "Hay to Gold"
        case .library: "Library"
        case .agents: "Agents"
        case .review: "Review"
        }
    }

    var icon: String {
        switch self {
        case .spin: "arrow.triangle.2.circlepath"
        case .library: "books.vertical"
        case .agents: "point.3.connected.trianglepath.dotted"
        case .review: "checklist"
        }
    }
}

enum VaultObjectType: String, CaseIterable, Identifiable {
    case workflow
    case prompt
    case profile
    case directory
    case bibliography
    case codexJob = "codex_job"
    case gold
    case skill
    case plugin
    case designMD = "design_md"
    case still
    case contextPack = "context_pack"
    case hay

    var id: String { rawValue }

    var title: String {
        switch self {
        case .workflow: "Workflow"
        case .prompt: "Prompt"
        case .profile: "Profile"
        case .directory: "Directory"
        case .bibliography: "Bibliography"
        case .codexJob: "Codex Job"
        case .gold: "Gold"
        case .skill: "Skill"
        case .plugin: "Plugin"
        case .designMD: "Design"
        case .still: "Still"
        case .contextPack: "Context Pack"
        case .hay: "Hay"
        }
    }
}

enum ProjectKind: String, CaseIterable, Codable, Identifiable {
    case generic
    case grantApplication
    case researchReport
    case localApp
    case researchMoat

    var id: String { rawValue }

    var label: String {
        switch self {
        case .generic: "Generic"
        case .grantApplication: "Grant/Application"
        case .researchReport: "Research/Report"
        case .localApp: "Local App"
        case .researchMoat: "Research Moat"
        }
    }
}

struct WorkbenchNote: Identifiable, Hashable {
    let id: UUID
    var title: String
    var body: String
    var path: URL
    var createdAt: Date
    var tags: [String]
}

struct WorkbenchProject: Identifiable, Codable, Hashable {
    var id: UUID
    var title: String
    var kind: ProjectKind
    var path: String
    var summary: String
    var updatedAt: Date
}

struct ReviewProposal: Identifiable, Hashable {
    enum Status: String {
        case pending
        case approved
        case rejected
    }

    let id: UUID
    var title: String
    var body: String
    var source: String
    var status: Status
    var path: URL
    var createdAt: Date
}

struct Runbook: Identifiable, Hashable {
    var id: String
    var title: String
    var detail: String
    var commandPreview: String
}

struct RegistrySnapshot: Hashable {
    var title: String
    var detail: String
    var fetchedAt: Date?
    var url: URL
    var status: String
}

struct VaultDocument: Identifiable, Hashable {
    let id: UUID
    var title: String
    var type: VaultObjectType
    var body: String
    var path: URL
    var createdAt: Date
    var status: String?
}

struct CodexJob: Identifiable, Hashable {
    let id: UUID
    var title: String
    var status: String
    var workflow: String
    var workingDirectory: String
    var writablePaths: [String]
    var sourcePaths: [String]
    var path: URL
    var createdAt: Date
    var exitCode: Int?
}

struct WorkbenchPaths {
    let vaultRoot: URL
    let libraryRoot: URL
    let workRoot: URL
    let systemRoot: URL
    let contextRoot: URL
    let knowledgeRoot: URL
    let assetsRoot: URL
    let inbox: URL
    let workflows: URL
    let prompts: URL
    let profile: URL
    let directories: URL
    let bibliography: URL
    let skills: URL
    let plugins: URL
    let design: URL
    let stills: URL
    let stillFiles: URL
    let contextPacks: URL
    let hay: URL
    let jobs: URL
    let projects: URL
    let review: URL
    let migrationReports: URL
    let runbooks: URL
    let gold: URL
    let supportRoot: URL
    let indexFile: URL
    let mcpServer: URL

    static var defaults: WorkbenchPaths {
        let home = FileManager.default.homeDirectoryForCurrentUser
        let vaultRoot = home
            .appendingPathComponent("Documents")
            .appendingPathComponent("Tremotino")
            .appendingPathComponent("Vault")
        let supportRoot = home
            .appendingPathComponent("Library")
            .appendingPathComponent("Application Support")
            .appendingPathComponent("Tremotino")
        let sourceFile = URL(fileURLWithPath: #filePath)
        let packageRoot = sourceFile
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
        let libraryRoot = vaultRoot.appendingPathComponent("Library")
        let workRoot = vaultRoot.appendingPathComponent("Work")
        let systemRoot = vaultRoot.appendingPathComponent("System")
        let contextRoot = libraryRoot.appendingPathComponent("Context")
        let knowledgeRoot = libraryRoot.appendingPathComponent("Knowledge")
        let assetsRoot = libraryRoot.appendingPathComponent("Assets")
        let stills = assetsRoot.appendingPathComponent("Stills")

        return WorkbenchPaths(
            vaultRoot: vaultRoot,
            libraryRoot: libraryRoot,
            workRoot: workRoot,
            systemRoot: systemRoot,
            contextRoot: contextRoot,
            knowledgeRoot: knowledgeRoot,
            assetsRoot: assetsRoot,
            inbox: workRoot.appendingPathComponent("Inbox"),
            workflows: contextRoot.appendingPathComponent("Workflows"),
            prompts: contextRoot.appendingPathComponent("Prompts"),
            profile: contextRoot.appendingPathComponent("Profile"),
            directories: contextRoot.appendingPathComponent("Directories"),
            bibliography: knowledgeRoot.appendingPathComponent("Bibliography"),
            skills: libraryRoot.appendingPathComponent("Skills"),
            plugins: assetsRoot.appendingPathComponent("Packs"),
            design: assetsRoot.appendingPathComponent("Design"),
            stills: stills,
            stillFiles: stills.appendingPathComponent("Files"),
            contextPacks: contextRoot.appendingPathComponent("Context Packs"),
            hay: workRoot.appendingPathComponent("Hay"),
            jobs: workRoot.appendingPathComponent("Jobs"),
            projects: knowledgeRoot.appendingPathComponent("Projects"),
            review: workRoot.appendingPathComponent("Review"),
            migrationReports: workRoot.appendingPathComponent("Migration Reports"),
            runbooks: systemRoot.appendingPathComponent("Runbooks"),
            gold: knowledgeRoot.appendingPathComponent("Gold"),
            supportRoot: supportRoot,
            indexFile: supportRoot.appendingPathComponent("index.json"),
            mcpServer: packageRoot.appendingPathComponent("mcp/tremotino_mcp.py")
        )
    }
}
