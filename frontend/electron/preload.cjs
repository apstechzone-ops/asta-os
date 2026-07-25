const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("asta", {
  version: process.versions.electron,
  platform: process.platform,
});
