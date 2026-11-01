#!/usr/bin/env -S deno run -A --env-file=../.env --watch=static/,routes/

import { load } from "@std/dotenv";

await load({ envPath: "../.env", export: true });

import dev from "$fresh/dev.ts";
import config from "./fresh.config.ts";

await dev(import.meta.url, "./main.ts", config);
