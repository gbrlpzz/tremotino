import SwiftUI

struct QuickCaptureView: View {
    @Environment(WorkbenchStore.self) private var store

    var body: some View {
        @Bindable var store = store

        VStack(alignment: .leading, spacing: 14) {
            Text("Quick Capture")
                .font(.title2)
                .fontWeight(.semibold)

            TextField("Title", text: $store.captureTitle)
                .textFieldStyle(.roundedBorder)

            TextEditor(text: $store.captureBody)
                .font(.body)
                .scrollContentBackground(.hidden)
                .background(.quaternary.opacity(0.5))
                .clipShape(RoundedRectangle(cornerRadius: 8))

            HStack {
                Text("Saved as Markdown in the vault inbox.")
                    .foregroundStyle(.secondary)
                Spacer()
                Button("Cancel") {
                    store.showQuickCapture = false
                }
                Button("Capture") {
                    store.saveCapture()
                }
                .keyboardShortcut(.defaultAction)
                .disabled(store.captureTitle.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && store.captureBody.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
        }
        .padding(20)
    }
}
