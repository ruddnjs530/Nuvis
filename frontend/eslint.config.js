import antfu from '@antfu/eslint-config';

export default antfu(
  {
    react: true,
    typescript: true,
    stylistic: {
      semi: true,
    },
    rules: {
      'no-empty-pattern': ['warn', { allowObjectPatternsAsParameters: true }],
      'no-console': 'warn',
      'ts/no-use-before-define': ['error', {
        functions: false,
        variables: false,
        typedefs: false,
        classes: true,
      }],
    },
  },
  {
    files: ["src/components/**/*.{js,jsx,ts,tsx}"],
    rules: {
      "react-refresh/only-export-components": "off",
    },
  },
  {
    ignores: ['**', '!src/**'],
  },
);
