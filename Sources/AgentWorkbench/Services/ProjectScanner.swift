import Foundation

struct ProjectScanner {
    func summarize(path: URL, kind: ProjectKind) -> String {
        let fileManager = FileManager.default
        let readme = ["README.md", "readme.md", "README.txt"]
            .map { path.appendingPathComponent($0) }
            .first { fileManager.fileExists(atPath: $0.path) }

        let readmeExcerpt: String
        if let readme, let content = try? String(contentsOf: readme, encoding: .utf8) {
            readmeExcerpt = String(content.prefix(1200))
        } else {
            readmeExcerpt = "No README found."
        }

        let packageHints = ["Package.swift", "package.json", "pyproject.toml", "requirements.txt"]
            .filter { fileManager.fileExists(atPath: path.appendingPathComponent($0).path) }
            .joined(separator: ", ")

        return """
        ## Project Summary Proposal

        - Path: \(path.path)
        - Kind: \(kind.label)
        - Detected files: \(packageHints.isEmpty ? "none" : packageHints)

        ## README Excerpt

        \(readmeExcerpt)

        ## Proposed Relations

        - relates_to [[Projects]]
        - source_folder \(path.path)
        """
    }
}
