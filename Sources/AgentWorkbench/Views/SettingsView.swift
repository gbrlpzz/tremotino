import SwiftUI

struct SettingsView: View {
    @Environment(WorkbenchStore.self) private var store
    @AppStorage("vaultBackupRemoteURL") private var vaultBackupRemoteURL = ""
    @State private var vaultBackupMessage = "Tremotino vault snapshot"

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

            Section("Private Vault Backup") {
                TextField("Private Git remote", text: $vaultBackupRemoteURL, prompt: Text("git@github.com:gbrlpzz/tremotino-vault.git"))
                    .textFieldStyle(.roundedBorder)
                TextField("Snapshot message", text: $vaultBackupMessage)
                    .textFieldStyle(.roundedBorder)

                HStack {
                    Button("Set Remote") {
                        store.configureVaultGitRemote(vaultBackupRemoteURL)
                    }
                    Button("Commit Snapshot") {
                        store.snapshotVaultGitBackup(message: vaultBackupMessage)
                    }
                    Button("Push Private Backup") {
                        store.pushVaultGitBackup()
                    }
                }

                Text("Backs up the private Markdown vault, not this public Tremotino source repository.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
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
