import { expect, test } from 'claude-code/testing'

const BAD_DOC = '# Create An API Key\n\n![](key.png)\n\nThe key is created by the system.\n'

test('/doclint reports the three rule violations', async ($, on) => {
  on('session.start', () => ({ cwd: '/work' }))
  on('command.register', () => ({ value: undefined }))
  on('fs.read', () => ({ value: BAD_DOC }))
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  const answer = await $.command.run({ command: 'doclint', args: 'docs/auth.md' })
  expect(answer.text).toContain('heading is not sentence case')
  expect(answer.text).toContain('image has no alt text')
  expect(answer.text).toContain('passive voice')
})

test('a clean file reports no issues', async ($, on) => {
  on('fs.read', () => ({ value: '# Create an API key\n\nYou create the key.\n' }))
  const answer = await $.command.run({ command: 'doclint', args: 'docs/ok.md' })
  expect(answer.text).toBe('No issues found')
})

test('editing a .md file puts the result in the band', async ($, on) => {
  on('tool.call', () => ({ result: 'ok' }))
  on('fs.read', () => ({ value: BAD_DOC }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: ['engine band'] }))
  await $.tool.call({ tool: 'Write', file_path: '/p/docs/auth.md' })
  const ui = await $.ui.mount({
    plugin: 'doc-lint-band', component: 'AbovePrompt', requestId: 'band',
    viewport: { columns: 100, rows: 30 }, props: {}, surface: 'terminal',
  })
  expect(await ui.find({ type: 'Text', text: /docs lint · auth\.md: 3 issue/ })).toBeDefined()
  await ui.unmount()
})
