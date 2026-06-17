const { contextBridge } = require('electron')

contextBridge.exposeInMainWorld('shianDesktop', {
  platform: process.platform,
  version: process.versions.electron
})
