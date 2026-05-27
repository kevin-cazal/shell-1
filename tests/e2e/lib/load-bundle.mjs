import { readFileSync } from "node:fs";
import { basename } from "node:path";
import { loadV86Bundle } from "../../../submodules/v86-runner/src/bundle/load.js";

/**
 * Load a .v86b bundle from disk (Node; no browser File API).
 * @param {string} bundlePath
 * @returns {Promise<import("../../../submodules/v86-runner/src/bundle/load.js").V86BundleLoadResult>}
 */
export async function loadBundleFromPath(bundlePath) {
  const buf = readFileSync(bundlePath);
  const file = { name: basename(bundlePath), size: buf.byteLength };

  const readSlice = async (start, length) => {
    const slice = buf.subarray(start, start + length);
    return slice.buffer.slice(
      slice.byteOffset,
      slice.byteOffset + slice.byteLength,
    );
  };

  return loadV86Bundle(file, { readSlice });
}
