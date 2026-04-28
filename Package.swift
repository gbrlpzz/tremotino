// swift-tools-version: 5.9

import PackageDescription

let package = Package(
    name: "Tremotino",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(name: "Tremotino", targets: ["Tremotino"])
    ],
    targets: [
        .executableTarget(
            name: "Tremotino",
            path: "Sources/AgentWorkbench"
        )
    ]
)
