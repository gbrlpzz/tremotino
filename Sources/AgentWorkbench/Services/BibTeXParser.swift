import Foundation

struct BibTeXEntry: Hashable {
    var type: String
    var key: String
    var fields: [String: String]
    var raw: String
}

enum BibTeXParser {
    static func parse(_ text: String) -> [BibTeXEntry] {
        splitEntries(text).compactMap(parseEntry)
    }

    private static func splitEntries(_ text: String) -> [String] {
        let scalars = Array(text)
        var entries: [String] = []
        var start: Int?
        var depth = 0
        var quoteOpen = false

        for index in scalars.indices {
            let character = scalars[index]
            if character == "@", start == nil {
                start = index
                depth = 0
                quoteOpen = false
            }

            guard start != nil else { continue }

            if character == "\"" {
                quoteOpen.toggle()
            } else if !quoteOpen {
                if character == "{" || character == "(" {
                    depth += 1
                } else if character == "}" || character == ")" {
                    depth -= 1
                    if depth == 0, let entryStart = start {
                        entries.append(String(scalars[entryStart...index]))
                        start = nil
                    }
                }
            }
        }

        return entries
    }

    private static func parseEntry(_ raw: String) -> BibTeXEntry? {
        guard let atIndex = raw.firstIndex(of: "@"),
              let openIndex = raw[atIndex...].firstIndex(where: { $0 == "{" || $0 == "(" }) else {
            return nil
        }

        let type = raw[raw.index(after: atIndex)..<openIndex]
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .lowercased()
        let closeIndex = raw.index(before: raw.endIndex)
        guard closeIndex > openIndex else { return nil }
        let body = String(raw[raw.index(after: openIndex)..<closeIndex])
        let parts = splitTopLevel(body, separator: ",", maxSplits: 1)
        guard let key = parts.first?.trimmingCharacters(in: .whitespacesAndNewlines), !key.isEmpty else {
            return nil
        }
        let fieldText = parts.count > 1 ? parts[1] : ""
        let fields = parseFields(fieldText)
        return BibTeXEntry(type: type, key: key, fields: fields, raw: raw.trimmingCharacters(in: .whitespacesAndNewlines))
    }

    private static func parseFields(_ text: String) -> [String: String] {
        var fields: [String: String] = [:]
        for part in splitTopLevel(text, separator: ",") {
            let assignment = splitTopLevel(part, separator: "=", maxSplits: 1)
            guard assignment.count == 2 else { continue }
            let key = assignment[0]
                .trimmingCharacters(in: .whitespacesAndNewlines)
                .lowercased()
            let value = cleanValue(assignment[1])
            if !key.isEmpty {
                fields[key] = value
            }
        }
        return fields
    }

    private static func splitTopLevel(_ text: String, separator: Character, maxSplits: Int? = nil) -> [String] {
        var parts: [String] = []
        var current = ""
        var braceDepth = 0
        var parenDepth = 0
        var quoteOpen = false
        var splits = 0

        for character in text {
            if character == "\"" {
                quoteOpen.toggle()
                current.append(character)
                continue
            }

            if !quoteOpen {
                if character == "{" {
                    braceDepth += 1
                } else if character == "}" {
                    braceDepth = max(0, braceDepth - 1)
                } else if character == "(" {
                    parenDepth += 1
                } else if character == ")" {
                    parenDepth = max(0, parenDepth - 1)
                }

                if character == separator, braceDepth == 0, parenDepth == 0, maxSplits.map({ splits < $0 }) ?? true {
                    parts.append(current)
                    current = ""
                    splits += 1
                    continue
                }
            }

            current.append(character)
        }

        parts.append(current)
        return parts
    }

    private static func cleanValue(_ raw: String) -> String {
        var value = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        if (value.hasPrefix("{") && value.hasSuffix("}")) || (value.hasPrefix("\"") && value.hasSuffix("\"")) {
            value.removeFirst()
            value.removeLast()
        }
        return value
            .replacingOccurrences(of: "\n", with: " ")
            .replacingOccurrences(of: "\\s+", with: " ", options: .regularExpression)
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
