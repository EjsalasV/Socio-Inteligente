module.exports = {
  root: true,
  extends: ["next/core-web-vitals"],
  overrides: [
    {
      files: ["**/*.ts", "**/*.tsx"],
      excludedFiles: ["lib/formatters.ts"],
      rules: {
        "no-restricted-syntax": [
          "error",
          {
            selector: "CallExpression[callee.property.name='toLocaleString']",
            message: "Usa formatMoney desde lib/formatters.ts para formato contable."
          },
          {
            selector: "NewExpression[callee.object.name='Intl'][callee.property.name='NumberFormat']",
            message: "Usa formatMoney desde lib/formatters.ts para formato contable."
          }
        ]
      }
    }
  ]
};
