import Foundation

struct TremotinoCoreClient {
    let paths: WorkbenchPaths

    func rebuildIndex() throws -> Int {
        let result = try run(command: "rebuild_index", arguments: [:])
        return result["indexed"] as? Int ?? 0
    }

    func migrateVaultDryRun() throws -> String {
        let result = try run(command: "migrate_vault", arguments: ["dry_run": true])
        if let reportPath = result["report_path"] as? String {
            return reportPath
        }
        return "Migration dry run completed"
    }

    private func run(command: String, arguments: [String: Any]) throws -> [String: Any] {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        let jsonData = try JSONSerialization.data(withJSONObject: arguments)
        let json = String(data: jsonData, encoding: .utf8) ?? "{}"
        process.arguments = ["-m", "tremotino_core", command, "--json", json]
        process.currentDirectoryURL = paths.mcpServer
            .deletingLastPathComponent()
            .deletingLastPathComponent()

        var environment = ProcessInfo.processInfo.environment
        environment["TREMOTINO_VAULT"] = paths.vaultRoot.path
        environment["TREMOTINO_SUPPORT"] = paths.supportRoot.path
        if let rootPath = process.currentDirectoryURL?.path {
            environment["PYTHONPATH"] = rootPath
        }
        process.environment = environment

        let output = Pipe()
        process.standardOutput = output
        process.standardError = output

        try process.run()
        let data = output.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()
        guard process.terminationStatus == 0 else {
            let text = String(data: data, encoding: .utf8) ?? "Core command failed"
            throw NSError(domain: "TremotinoCore", code: Int(process.terminationStatus), userInfo: [NSLocalizedDescriptionKey: text])
        }
        let object = try JSONSerialization.jsonObject(with: data)
        guard let dictionary = object as? [String: Any] else {
            throw NSError(domain: "TremotinoCore", code: -1, userInfo: [NSLocalizedDescriptionKey: "Core returned non-object JSON"])
        }
        return dictionary
    }
}
