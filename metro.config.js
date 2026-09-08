const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require("nativewind/metro");

const config = getDefaultConfig(__dirname);

// Exclude backend and temporary workspace directories from Metro's watch list
// This prevents Metro from crashing when the backend creates/deletes temp folders
config.resolver.blockList = [
  /.*loom-workspaces.*/,
  /.*backend\/venv.*/,
  /.*backend\/__pycache__.*/,
];

module.exports = withNativeWind(config, { input: "./src/global.css" });
