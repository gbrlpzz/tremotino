import Foundation

enum SidebarItem: String, CaseIterable, Identifiable {
    case inbox
    case projects
    case review
    case runbooks
    case registry
    case settings

    var id: String { rawValue }

    var title: String {
        switch self {
        case .inbox: "Inbox"
        case .projects: "Projects"
        case .review: "Review Queue"
        case .runbooks: "Runbooks"
        case .registry: "Registry"
        case .settings: "Settings"
        }
    }

    var icon: String {
        switch self {
        case .inbox: "tray"
        case .projects: "folder"
        case .review: "checklist"
        case .runbooks: "play.square"
        case .registry: "antenna.radiowaves.left.and.right"
        case .settings: "gearshape"
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

struct WorkbenchPaths {
    let vaultRoot: URL
    let inbox: URL
    let projects: URL
    let review: URL
    let runbooks: URL
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
            projects: vaultRoot.appendingPathComponent("Projects"),
            review: vaultRoot.appendingPathComponent("Review Queue"),
            runbooks: vaultRoot.appendingPathComponent("Runbooks"),
            supportRoot: supportRoot,
            indexFile: supportRoot.appendingPathComponent("index.json"),
            mcpServer: packageRoot.appendingPathComponent("mcp/tremotino_mcp.py")
        )
    }
}
