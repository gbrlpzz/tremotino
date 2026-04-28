import Foundation

enum SidebarItem: String, CaseIterable, Identifiable {
    case capture
    case spin
    case review
    case library
    case settings

    var id: String { rawValue }

    var title: String {
        switch self {
        case .capture: "Capture"
        case .spin: "Hay to Gold"
        case .review: "Review"
        case .library: "Agent Hub"
        case .settings: "Settings"
        }
    }

    var icon: String {
        switch self {
        case .capture: "tray.and.arrow.down"
        case .spin: "arrow.triangle.2.circlepath"
        case .review: "checklist"
        case .library: "point.3.connected.trianglepath.dotted"
        case .settings: "gearshape"
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

        return WorkbenchPaths(
            vaultRoot: vaultRoot,
            inbox: vaultRoot.appendingPathComponent("Inbox"),
            workflows: vaultRoot.appendingPathComponent("Workflows"),
            prompts: vaultRoot.appendingPathComponent("Prompts"),
            profile: vaultRoot.appendingPathComponent("Profile"),
            directories: vaultRoot.appendingPathComponent("Directories"),
            bibliography: vaultRoot.appendingPathComponent("Bibliography"),
            skills: vaultRoot.appendingPathComponent("Skills"),
            plugins: vaultRoot.appendingPathComponent("Plugins"),
            design: vaultRoot.appendingPathComponent("Design"),
            stills: vaultRoot.appendingPathComponent("Stills"),
            stillFiles: vaultRoot.appendingPathComponent("Stills").appendingPathComponent("Files"),
            contextPacks: vaultRoot.appendingPathComponent("Context Packs"),
            hay: vaultRoot.appendingPathComponent("Hay"),
            jobs: vaultRoot.appendingPathComponent("Jobs"),
            projects: vaultRoot.appendingPathComponent("Projects"),
            review: vaultRoot.appendingPathComponent("Review Queue"),
            runbooks: vaultRoot.appendingPathComponent("Runbooks"),
            gold: vaultRoot.appendingPathComponent("Gold"),
            supportRoot: supportRoot,
            indexFile: supportRoot.appendingPathComponent("index.json"),
            mcpServer: packageRoot.appendingPathComponent("mcp/tremotino_mcp.py")
        )
    }
}
