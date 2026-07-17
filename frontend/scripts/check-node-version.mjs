const supported = [
  { major: 20, minMinor: 19 },
  { major: 22, minMinor: 12 }
]

const [major, minor] = process.versions.node.split('.').map(Number)
const ok = supported.some((range) => major === range.major && minor >= range.minMinor)

if (!ok) {
  console.error(
    `Unsupported Node ${process.versions.node}. Use Node 20.19.x or Node 22.12.x+ for the frontend.`
  )
  process.exit(1)
}
