// doc-lint-band: a mod that lints Markdown after Claude writes it,
// and shows the result in a band above the prompt.

// Latest result, shared by the hooks below: { file, issues: string[] } or null
let last = null

// The same three rules as the hook in the mini-plugin, as a pure function
export function lint(text) {
  const issues = []
  let inCode = false
  text.split('\n').forEach((line, i) => {
    const n = i + 1
    if (line.trim().startsWith('```')) { inCode = !inCode; return }
    if (inCode) return
    const h = line.match(/^#{1,6}\s+(.*)$/)
    if (h) {
      const caps = h[1].split(/\s+/).slice(1).filter((w) => /^[A-Z]/.test(w) && w !== w.toUpperCase())
      if (caps.length >= 2) issues.push(`line ${n}: heading is not sentence case`)
    }
    if (/!\[\]\(/.test(line)) issues.push(`line ${n}: image has no alt text`)
    if (/\b(is|are|was|were|been|being)\s+\w+ed\s+by\b/i.test(line)) issues.push(`line ${n}: passive voice`)
  })
  return issues
}

export function register(on) {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'doclint', description: 'Lint a Markdown file: /doclint docs/auth.md' })
    return next(e)
  })

  // After Claude writes or edits a .md file, lint it and update the band
  on('tool.call', async ($, e, next) => {
    const result = await next(e) // let the tool run first
    const isWrite = e.tool === 'Write' || e.tool === 'Edit'
    if (isWrite && typeof e.file_path === 'string' && e.file_path.endsWith('.md')) {
      const text = await $.fs.read(e.file_path)
      last = { file: e.file_path.split('/').pop(), issues: lint(text) }
      $.ui.invalidate('ui.render')
    }
    return result
  })

  // /doclint <file>: lint on demand, no Claude turn
  on('command.run', { command: 'doclint' }, async ($, e) => {
    const file = e.args.trim()
    if (!file) return { text: 'Usage: /doclint <file.md>' }
    const issues = lint(await $.fs.read(file))
    last = { file: file.split('/').pop(), issues }
    $.ui.invalidate('ui.render')
    return { text: issues.length ? issues.join('\n') : 'No issues found' }
  })

  // The band above the prompt: show nothing until there is a result
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (!last) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    const bad = last.issues.length > 0
    return Box({
      flexDirection: 'column',
      children: [
        Text({
          color: bad ? 'red' : 'green',
          children: [`docs lint · ${last.file}: ${bad ? last.issues.length + ' issue(s)' : 'clean'}`],
        }),
        await next(e), // keep whatever other mods draw in the band
      ],
    })
  })
}
