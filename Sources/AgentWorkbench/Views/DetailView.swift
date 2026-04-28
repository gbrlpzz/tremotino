import SwiftUI

struct DetailView: View {
    @Environment(WorkbenchStore.self) private var store

    var body: some View {
        switch store.selection ?? .library {
        case .spin:
            SpinView()
        case .library:
            LibraryView()
        case .agents:
            AgentsView()
        case .review:
            ReviewQueueView()
        }
    }
}
