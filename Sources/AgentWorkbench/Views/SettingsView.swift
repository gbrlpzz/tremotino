import SwiftUI

struct SettingsView: View {
    @Environment(WorkbenchStore.self) private var store

    var body: some View {
        Form {
            Section("Storage") {
                LabeledContent("Vault") {
                    Text(store.paths.vaultRoot.path)
                        .textSelection(.enabled)
                }
                LabeledContent("Index") {
                    Text(store.paths.indexFile.path)
                        .textSelection(.enabled)
                }
                Button("Initialize Vault Git Backup") {
                    store.initializeVaultGitBackup()
                }
            }

            Section("MCP") {
                LabeledContent("Server") {
                    Text(store.paths.mcpServer.path)
                        .textSelection(.enabled)
                }
                LabeledContent("Health") {
                    Text(store.mcpHealth)
                        .textSelection(.enabled)
                }
            }

            Section("Policy") {
                LabeledContent("Write policy", value: "Review queue")
                LabeledContent("Required clients", value: "Codex + Claude")
                LabeledContent("Cloud backend", value: "None")
            }
        }
        .formStyle(.grouped)
        .padding()
    }
}
