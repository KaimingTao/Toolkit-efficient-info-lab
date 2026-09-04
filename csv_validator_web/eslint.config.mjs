/* CSV validator web workflow lint configuration. See index.md for the
   browser workflow that this configuration validates. */

import js from "@eslint/js";

export default [
  js.configs.recommended,
  {
    rules: {
      "no-control-regex": "off",
    },
    languageOptions: {
      globals: {
        Blob: "readonly",
        FileReader: "readonly",
        TextDecoder: "readonly",
        URL: "readonly",
        document: "readonly",
      },
    },
  },
];
