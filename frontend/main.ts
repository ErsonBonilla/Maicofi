import { load } from "@std/dotenv";

await load({ envPath: "../.env", export: true });

import { start } from "$fresh/server.ts";
import manifest from "./fresh.gen.ts";
import config from "./fresh.config.ts";

await start(manifest, config);
