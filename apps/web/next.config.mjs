/** @type {import('next').NextConfig} */
const nextConfig = {
  // "standalone" for the Docker web deployment (default), "export" for the
  // Tauri desktop build — set BUILD_TARGET=desktop to produce static files.
  output: process.env.BUILD_TARGET === "desktop" ? "export" : "standalone",
}

export default nextConfig
