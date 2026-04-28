import SwiftUI

private enum AgentsTab: String, CaseIterable, Identifiable {
    case context
    case jobs
    case mcp
    case backup

    var id: String { rawValue }

    var title: String {
        switch self {
        case .context: "Context"
        case .jobs: "Jobs"
        case .mcp: "MCP"
        case .backup: "Backup"
        }
    }
}

struct AgentsView: View {
    @Environment(WorkbenchStore.self) private var store
    @State private var selectedTab: AgentsTab = .context
    @AppStorage("vaultBackupRemoteURL") private var vaultBackupRemoteURL = ""
    @State private var vaultBackupMessage = "Tremotino vault snapshot"

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HeaderView(
                title: "Agents",
                subtitle: "MCP wiring, context packs, skill sync, Codex jobs, and private vault backup."
            )

            Picker("Agent section", selection: $selectedTab) {
                ForEach(AgentsTab.allCases) { tab in
                    Text(tab.title).tag(tab)
                }
            }
            .pickerStyle(.segmented)

            switch selectedTab {
            case .context:
                TypedDocumentsView(type: .contextPack, showsHeader: false)
            case .jobs:
                JobsView(showsHeader: false)
            case .mcp:
                mcpPanel
            case .backup:
                backupPanel
            }

            FooterStatusView()
        }
        .padding()
    }

    private var mcpPanel: some View {
        Form {
            Section("MCP") {
                LabeledContent("Server") {
                    Text(store.paths.mcpServer.path)
                        .textSelection(.enabled)
                }
                LabeledContent("Health") {
                    Text(store.mcpHealth)
                        .textSelection(.enabled)
                }
                Button("Sync Cross-Agent Skills") {
                    store.syncSkills()
                }
                Button("Rebuild Index") {
                    Task { await store.rebuildIndex() }
                }
            }

            Section("Vault") {
                LabeledContent("Root") {
                    Text(store.paths.vaultRoot.path)
                        .textSelection(.enabled)
                }
                LabeledContent("SQLite Index") {
                    Text(store.paths.supportRoot.appendingPathComponent("index.sqlite").path)
                        .textSelection(.enabled)
                }
            }
        }
        .formStyle(.grouped)
    }

    private var backupPanel: some View {
        Form {
            Section("Private Vault Backup") {
                TextField("Private Git remote", text: $vaultBackupRemoteURL, prompt: Text("git@github.com:gbrlpzz/tremotino-vault.git"))
                    .textFieldStyle(.roundedBorder)
                TextField("Snapshot message", text: $vaultBackupMessage)
                    .textFieldStyle(.roundedBorder)

                HStack {
                    Button("Initialize") {
                        store.initializeVaultGitBackup()
                    }
                    Button("Set Remote") {
                        store.configureVaultGitRemote(vaultBackupRemoteURL)
                    }
                    Button("Commit Snapshot") {
                        store.snapshotVaultGitBackup(message: vaultBackupMessage)
                    }
                    Button("Push") {
                        store.pushVaultGitBackup()
                    }
                }
            }
        }
        .formStyle(.grouped)
    }
}
