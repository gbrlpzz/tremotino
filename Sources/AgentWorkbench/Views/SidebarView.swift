import SwiftUI

struct SidebarView: View {
    @Binding var selection: SidebarItem?

    var body: some View {
        List(selection: $selection) {
            ForEach(SidebarItem.allCases) { item in
                Label(item.title, systemImage: item.icon)
                    .tag(item)
            }
        }
        .listStyle(.sidebar)
        .navigationTitle("Tremotino")
    }
}
