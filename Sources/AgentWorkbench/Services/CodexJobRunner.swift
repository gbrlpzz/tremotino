import Foundation

struct CodexJobRunner {
    let vaultRoot: URL

    func run(job: CodexJob) async -> Int32 {
        let folder = job.path.deletingLastPathComponent()
        let promptFile = folder.appendingPathComponent("prompt.md")
        let eventsFile = folder.appendingPathComponent("events.jsonl")
        let finalFile = folder.appendingPathComponent("final.md")
        let preSnapshot = folder.appendingPathComponent("pre_snapshot.txt")
        let postSnapshot = folder.appendingPathComponent("post_snapshot.txt")

        writeSnapshot(to: preSnapshot)

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/opt/homebrew/bin/codex")
        var arguments = [
            "exec",
            "-m", "gpt-5.2",
            "--cd", job.workingDirectory,
            "--skip-git-repo-check",
            "--sandbox", "workspace-write",
            "--add-dir", vaultRoot.path
        ]
        for writable in job.writablePaths where writable != vaultRoot.path && !writable.isEmpty {
            arguments.append(contentsOf: ["--add-dir", NSString(string: writable).expandingTildeInPath])
        }
        for source in job.sourcePaths where source != vaultRoot.path && !source.isEmpty {
            arguments.append(contentsOf: ["--add-dir", NSString(string: source).expandingTildeInPath])
        }
        arguments.append(contentsOf: [
            "--json",
            "--output-last-message", finalFile.path,
            "-"
        ])
        process.arguments = arguments

        let input = Pipe()
        let output = Pipe()
        let error = Pipe()
        process.standardInput = input
        process.standardOutput = output
        process.standardError = error

        do {
            try process.run()
            if let promptData = try? Data(contentsOf: promptFile) {
                input.fileHandleForWriting.write(promptData)
            }
            input.fileHandleForWriting.closeFile()

            let outputData = output.fileHandleForReading.readDataToEndOfFile()
            let errorData = error.fileHandleForReading.readDataToEndOfFile()
            var combined = Data()
            combined.append(outputData)
            if !errorData.isEmpty {
                combined.append("\n".data(using: .utf8) ?? Data())
                combined.append(errorData)
            }
            try combined.write(to: eventsFile, options: .atomic)
            process.waitUntilExit()
        } catch {
            let message = "Failed to run Codex job: \(error.localizedDescription)\n"
            try? message.write(to: eventsFile, atomically: true, encoding: .utf8)
            writeSnapshot(to: postSnapshot)
            return -1
        }

        writeSnapshot(to: postSnapshot)
        return process.terminationStatus
    }

    private func writeSnapshot(to url: URL) {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/git")
        process.arguments = ["status", "--short"]
        process.currentDirectoryURL = vaultRoot
        let output = Pipe()
        process.standardOutput = output
        process.standardError = output

        do {
            try ensureVaultGit()
            try process.run()
            let data = output.fileHandleForReading.readDataToEndOfFile()
            process.waitUntilExit()
            let header = "Vault: \(vaultRoot.path)\nDate: \(ISO8601DateFormatter().string(from: Date()))\n\n"
            var combined = Data(header.utf8)
            combined.append(data)
            try combined.write(to: url, options: .atomic)
        } catch {
            let fallback = "Snapshot failed: \(error.localizedDescription)\n"
            try? fallback.write(to: url, atomically: true, encoding: .utf8)
        }
    }

    private func ensureVaultGit() throws {
        if FileManager.default.fileExists(atPath: vaultRoot.appendingPathComponent(".git").path) {
            return
        }
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/git")
        process.arguments = ["init"]
        process.currentDirectoryURL = vaultRoot
        try process.run()
        process.waitUntilExit()
    }
}
