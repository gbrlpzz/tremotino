import SwiftUI

@main
struct AgentWorkbenchApp: App {
    @State private var store = WorkbenchStore()

    var body: some Scene {
        WindowGroup("Tremotino", id: "main") {
            ContentView()
                .environment(store)
                .task {
                    await store.bootstrap()
                }
        }
        .commands {
            CommandMenu("Workbench") {
                Button("Quick Capture") {
                    store.showQuickCapture = true
                }
                .keyboardShortcut("n", modifiers: [.command, .shift])

                Button("Rebuild Index") {
                    Task { await store.rebuildIndex() }
                }
                .keyboardShortcut("r", modifiers: [.command, .shift])
            }
        }

        Settings {
            SettingsView()
                .environment(store)
        }
    }
}
