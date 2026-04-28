import SwiftUI

struct ContentView: View {
    @Environment(WorkbenchStore.self) private var store

    var body: some View {
        @Bindable var store = store

        NavigationSplitView {
            SidebarView(selection: $store.selection)
        } detail: {
            DetailView()
        }
        .sheet(isPresented: $store.showQuickCapture) {
            QuickCaptureView()
                .frame(width: 520, height: 380)
        }
        .toolbar {
            ToolbarItemGroup {
                Button {
                    store.showQuickCapture = true
                } label: {
                    Label("Capture", systemImage: "square.and.pencil")
                }

                Button {
                    Task { await store.rebuildIndex() }
                } label: {
                    Label("Rebuild Index", systemImage: "arrow.triangle.2.circlepath")
                }
            }
        }
    }
}
