import { execSync } from "node:child_process";
import { resolve } from "node:path";

const root = resolve(process.cwd(), "..");
const input = resolve(root, "backend", "openapi.json");
const output = resolve(process.cwd(), "lib", "types.ts");

execSync(`npx openapi-typescript \"${input}\" -o \"${output}\"`, { stdio: "inherit" });
console.log(`Generated ${output}`);
